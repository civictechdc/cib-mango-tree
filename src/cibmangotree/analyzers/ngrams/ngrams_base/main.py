import os
from concurrent.futures import ProcessPoolExecutor
from math import ceil
from pathlib import Path
from tempfile import TemporaryDirectory

import polars as pl

from cibmangotree.analyzer_interface.context import (
    NullProgressReporter,
    PrimaryAnalyzerContext,
)
from cibmangotree.services.tokenizer.basic import TokenizerConfig, tokenize_text
from cibmangotree.services.tokenizer.core.types import CaseHandling

from .interface import (
    COL_AUTHOR_ID,
    COL_MESSAGE_ID,
    COL_MESSAGE_SURROGATE_ID,
    COL_MESSAGE_TEXT,
    COL_MESSAGE_TIMESTAMP,
    COL_NGRAM_ID,
    COL_NGRAM_LENGTH,
    COL_NGRAM_WORDS,
    OUTPUT_MESSAGE,
    OUTPUT_MESSAGE_NGRAMS,
    OUTPUT_NGRAM_DEFS,
    PARAM_MAX_N,
    PARAM_MIN_N,
)


def _preprocess_messages(df_input: pl.DataFrame) -> pl.DataFrame:
    """
    Add surrogate IDs and filter invalid messages.

    Args:
        df_input: Raw input dataframe with message data

    Returns:
        Preprocessed dataframe with:
        - message_surrogate_id column added (1-indexed)
        - null/empty message_text filtered out
        - null/empty author_id filtered out
    """
    df_input = df_input.with_columns(
        (pl.int_range(pl.len()) + 1).alias(COL_MESSAGE_SURROGATE_ID)
    )
    df_input = df_input.filter(
        pl.col(COL_MESSAGE_TEXT).is_not_null()
        & (pl.col(COL_MESSAGE_TEXT) != "")
        & pl.col(COL_AUTHOR_ID).is_not_null()
        & (pl.col(COL_AUTHOR_ID) != "")
    )
    return df_input


# Below this many messages, process startup is more work than we save by parallelizing.
MIN_ROWS_FOR_PARALLEL = 5_000

# Several chunks per worker so uneven message lengths still balance across cores.
CHUNKS_PER_WORKER = 4

# Chunks submitted per worker in one wave. Bounds how many results can be in flight
# at once without starving workers between waves
CHUNKS_PER_WAVE = 2

# Internal only, identifies an n-gram while its text is not being carried
COL_NGRAM_HASH = "ngram_hash"

# Fixed so hashes are identical across worker processes runs. Polars' hash is
# stable for a given seed, but Python's hash() is not because of PYTHONHASHSEED
# randomisation, must not be used here
NGRAM_HASH_SEED = 0


def _emit_ngram_pairs(
    payload: tuple[list[int], list[str], int, int, TokenizerConfig],
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Tokenize a chunk of messages and emit one row per (message, distinct n-gram).

    Intended to be dispatched to worker processes, and thus only takes picklable
    arguments. It does not assign n-gram ids at this stage, in order to avoid
    a cross-chunk counter.

    The occurrence table identifies each n-gram by hash rather than text, which
    is returned separately once per n-gram per chunk. This avoids having to
    hold a copy of every n-gram string per message it appears in, which is
    prohibitive on large corpuses. This also allows us to group and join on
    integers rather than strings

    Args:
        payload: (surrogate_ids, texts, min_n, max_n, tokenizer_config)

    Returns:
        (df_pairs, df_chunk_defs) where
        - df_pairs: columns [message_surrogate_id, ngram_hash]
        - df_chunk_defs: columns [ngram_hash, words], distinct within this chunk
    """
    surrogate_ids, texts, min_n, max_n, tokenizer_config = payload

    out_surrogate_ids: list[int] = []
    out_words: list[str] = []

    for surrogate_id, text in zip(surrogate_ids, texts):
        tokens = tokenize_text(text, tokenizer_config)

        # this will track within message repetitions
        seen_ngrams_in_message = set()

        for ngram in ngrams(tokens, min_n, max_n):
            serialized_ngram = serialize_ngram(ngram)

            # skip repetitions of already detected ngrams
            if serialized_ngram in seen_ngrams_in_message:
                continue
            seen_ngrams_in_message.add(serialized_ngram)

            out_surrogate_ids.append(surrogate_id)
            out_words.append(serialized_ngram)

    df_chunk = pl.DataFrame(
        {
            COL_MESSAGE_SURROGATE_ID: pl.Series(out_surrogate_ids, dtype=pl.Int64),
            COL_NGRAM_WORDS: pl.Series(out_words, dtype=pl.String),
        }
    ).with_columns(
        pl.col(COL_NGRAM_WORDS).hash(seed=NGRAM_HASH_SEED).alias(COL_NGRAM_HASH)
    )

    return (
        df_chunk.select(COL_MESSAGE_SURROGATE_ID, COL_NGRAM_HASH),
        # deduplicated on (hash, text) rather than hash alone
        # collapsing on the hash here would hide a collision instead of
        # letting the caller detect one
        df_chunk.select(COL_NGRAM_HASH, COL_NGRAM_WORDS).unique(),
    )


def _spill_chunks(
    payloads: list[tuple],
    max_workers: int,
    spill_dir: Path,
    progress_callback=None,
) -> None:
    """
    Run _emit_ngram_pairs over payloads, writing each chunk's result straight to
    parquet in `spill_dir` instead of returning it.

    Work is submitted in bounded waves rather than all at once. `Future` objects hold
    a reference to their result until they are themselves released, so submitting
    everything up front would re-accumulate the whole table no matter how promptly
    each result is written.
    """
    total = len(payloads)
    done = 0

    def _write(index: int, result: tuple[pl.DataFrame, pl.DataFrame]) -> None:
        pairs, defs = result
        pairs.write_parquet(spill_dir / f"pairs_{index:06d}.parquet")
        defs.write_parquet(spill_dir / f"defs_{index:06d}.parquet")

    if max_workers <= 1:
        for index, payload in enumerate(payloads):
            _write(index, _emit_ngram_pairs(payload))
            done += 1
            if progress_callback:
                progress_callback(done / total)
        return

    wave_size = max_workers * CHUNKS_PER_WAVE
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for base in range(0, total, wave_size):
            wave = payloads[base : base + wave_size]
            for offset, result in enumerate(executor.map(_emit_ngram_pairs, wave)):
                _write(base + offset, result)
                del result
                done += 1
                if progress_callback:
                    progress_callback(done / total)


def _subspans_of_longer_ngrams(
    surviving_defs: pl.DataFrame, min_n: int
) -> pl.DataFrame | None:
    """
    Proper contiguous subspans of each surviving n-gram longer than min_n.

    Only subspans that are themselves repeated are returned. A child that
    appears in just one message is already excluded from the output.

    Returns columns [parent_hash, child_hash], or None when there is nothing
    to remove.
    """
    longer = surviving_defs.filter(pl.col(COL_NGRAM_LENGTH) > min_n)
    if longer.is_empty():
        return None

    parent_hashes: list[int] = []
    child_words: list[str] = []
    for words, parent_hash, n in longer.select(
        COL_NGRAM_WORDS, COL_NGRAM_HASH, COL_NGRAM_LENGTH
    ).iter_rows():
        tokens = words.split(" ")
        for length in range(min_n, n):
            for start in range(n - length + 1):
                parent_hashes.append(parent_hash)
                child_words.append(" ".join(tokens[start : start + length]))

    hash_dtype = longer.schema[COL_NGRAM_HASH]
    subspans = (
        pl.DataFrame(
            {
                "parent_hash": pl.Series(parent_hashes, dtype=hash_dtype),
                "child_words": pl.Series(child_words, dtype=pl.String),
            }
        )
        .with_columns(
            pl.col("child_words").hash(seed=NGRAM_HASH_SEED).alias("child_hash")
        )
        .join(
            surviving_defs.select(pl.col(COL_NGRAM_HASH).alias("child_hash")),
            on="child_hash",
            how="inner",
        )
    )
    if subspans.is_empty():
        return None
    return subspans.select("parent_hash", "child_hash").unique()


def _drop_subsumed_occurrences(
    pairs: pl.LazyFrame,
    chunk_defs: pl.LazyFrame,
    surviving_hashes: pl.LazyFrame,
    min_n: int,
) -> tuple[pl.LazyFrame, pl.LazyFrame]:
    """
    Drop a shorter n-gram from a message when that message also contains a
    longer n-gram that repeats across messages, and the shorter one is a
    contiguous subspan of it.

    Occurrences in other messages are kept. Hashes that then occur in only one
    message are dropped, matching the filter applied before this step.
    """
    surviving_defs = (
        chunk_defs.unique(subset=COL_NGRAM_HASH)
        .join(surviving_hashes.select(COL_NGRAM_HASH), on=COL_NGRAM_HASH, how="inner")
        .with_columns(
            pl.col(COL_NGRAM_WORDS).str.split(" ").list.len().alias(COL_NGRAM_LENGTH)
        )
        .collect(engine="streaming")
    )
    subspans = _subspans_of_longer_ngrams(surviving_defs, min_n)
    if subspans is None:
        return pairs, surviving_hashes

    covered = (
        pairs.join(
            subspans.lazy(),
            left_on=COL_NGRAM_HASH,
            right_on="parent_hash",
            how="inner",
        )
        .select(
            COL_MESSAGE_SURROGATE_ID,
            pl.col("child_hash").alias(COL_NGRAM_HASH),
        )
        .unique()
    )
    pairs = pairs.join(
        covered,
        on=[COL_MESSAGE_SURROGATE_ID, COL_NGRAM_HASH],
        how="anti",
    )
    surviving_hashes = pairs.group_by(COL_NGRAM_HASH).len().filter(pl.col("len") > 1)
    return pairs, surviving_hashes


def _extract_ngrams_from_messages(
    df_input: pl.DataFrame,
    min_n: int,
    max_n: int,
    tokenizer_config: TokenizerConfig,
    progress_callback=None,
    max_workers: int | None = None,
    spill_dir: str | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Extract n-grams from messages with within-message deduplication.

    N-grams occurring in only one message are dropped immediately. These make up
    the great majority of distinct n-grams on a typical corpus.

    A shorter n-gram is then removed from a message when that message contains
    a longer repeated n-gram of which it is a contiguous subspan. Counts are
    recomputed, so the shorter n-gram is kept when other messages contain it
    without the longer phrase.

    Intermediate results are written to disk and read back lazily rather than being
    held in memory: the occurrence table is much larger than either output derived
    from it, and on a large corpus keeping it resident dominates the analyzer's
    memory use.

    Args:
        df_input: Preprocessed dataframe with messages
        min_n: Minimum n-gram length
        max_n: Maximum n-gram length
        tokenizer_config: Configuration for text tokenization
        progress_callback: Optional callback for progress reporting
        max_workers: Worker processes to use. Defaults to one per available core.
        spill_dir: Directory to place scratch files under. Defaults to the system
            temp location. Files are removed before this function returns.

    Returns:
        Tuple of (df_message_ngrams, df_ngram_defs) where:
        - df_message_ngrams: DataFrame with columns [message_surrogate_id, ngram_id]
        - df_ngram_defs: DataFrame with columns [ngram_id, words, n]
    """
    surrogate_ids = df_input[COL_MESSAGE_SURROGATE_ID].to_list()
    texts = df_input[COL_MESSAGE_TEXT].to_list()

    if max_workers is None:
        max_workers = os.cpu_count() or 1
    if df_input.height < MIN_ROWS_FOR_PARALLEL:
        max_workers = 1

    n_chunks = 1 if max_workers <= 1 else max_workers * CHUNKS_PER_WORKER
    chunk_size = max(1, ceil(df_input.height / n_chunks))
    payloads = [
        (
            surrogate_ids[start : start + chunk_size],
            texts[start : start + chunk_size],
            min_n,
            max_n,
            tokenizer_config,
        )
        for start in range(0, df_input.height, chunk_size)
    ]

    if not payloads:
        return _empty_message_ngrams_frame(), _empty_ngram_defs_frame()

    # Spill under the analyzer's temp dir when one was supplied, so the scratch files
    # land on the same volume the rest of the run uses and are cleaned up with it.
    with TemporaryDirectory(dir=spill_dir) as tmp:
        spill_path = Path(tmp)
        _spill_chunks(payloads, max_workers, spill_path, progress_callback)

        pairs = pl.scan_parquet(spill_path / "pairs_*.parquet")
        chunk_defs = pl.scan_parquet(spill_path / "defs_*.parquet")

        _assert_no_hash_collisions(chunk_defs)

        # Grouping and filtering happen on the hash, so neither touches string data.
        surviving_hashes = (
            pairs.group_by(COL_NGRAM_HASH).len().filter(pl.col("len") > 1)
        )
        pairs, surviving_hashes = _drop_subsumed_occurrences(
            pairs, chunk_defs, surviving_hashes, min_n
        )

        # One row per n-gram that survives, rather than one per occurrence: this is
        # the only place the text is materialised.
        # Sorting before assigning ids keeps ngram_id stable across runs, since
        # group_by output order is not deterministic and the ids feed the sort order
        # of the outputs.
        df_ngram_defs = (
            chunk_defs.unique(subset=COL_NGRAM_HASH)
            .join(
                surviving_hashes.select(COL_NGRAM_HASH),
                on=COL_NGRAM_HASH,
                how="inner",
            )
            .collect(engine="streaming")
            .sort(COL_NGRAM_WORDS)
            .with_row_index(COL_NGRAM_ID)
            .with_columns(
                pl.col(COL_NGRAM_ID).cast(pl.Int64),
                pl.col(COL_NGRAM_WORDS)
                .str.split(" ")
                .list.len()
                .alias(COL_NGRAM_LENGTH),
            )
        )

        df_message_ngrams = (
            pairs.join(
                df_ngram_defs.lazy().select(COL_NGRAM_HASH, COL_NGRAM_ID),
                on=COL_NGRAM_HASH,
                how="inner",
            )
            .select(COL_MESSAGE_SURROGATE_ID, COL_NGRAM_ID)
            .collect(engine="streaming")
        )

    return df_message_ngrams, df_ngram_defs.select(
        COL_NGRAM_ID, COL_NGRAM_WORDS, COL_NGRAM_LENGTH
    )


def _assert_no_hash_collisions(chunk_defs: pl.LazyFrame) -> None:
    """
    Guard the assumption that a hash identifies exactly one n-gram.

    Though unlikely, two n-grams sharing a hash would break us, and via the
    birthday paradox, the chance of overlap across a few million n-grams is
    higher than you may expect.

    Chunks emit (hash, text) pairs already deduplicated, so a hash appearing
    more than once here means two different n-grams produced it. Checking it
    this way groups on the hash alone instead of making a large number of
    string comparisons
    """
    collisions = (
        chunk_defs.unique()
        .group_by(COL_NGRAM_HASH)
        .len()
        .filter(pl.col("len") > 1)
        .head(1)
        .collect(engine="streaming")
    )
    if not collisions.is_empty():
        raise RuntimeError(
            "n-gram hash collision detected: two distinct n-grams share the hash "
            f"{collisions[0, COL_NGRAM_HASH]}. Their occurrence counts would be "
            "merged, so the run has been stopped rather than produce incorrect "
            "results."
        )


def _empty_message_ngrams_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            COL_MESSAGE_SURROGATE_ID: pl.Series([], dtype=pl.Int64),
            COL_NGRAM_ID: pl.Series([], dtype=pl.Int64),
        }
    )


def _empty_ngram_defs_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            COL_NGRAM_ID: pl.Series([], dtype=pl.Int64),
            COL_NGRAM_WORDS: pl.Series([], dtype=pl.String),
            COL_NGRAM_LENGTH: pl.Series([], dtype=pl.UInt32),
        }
    )


def main(context: PrimaryAnalyzerContext):
    progress = context.progress_reporter or (lambda name: NullProgressReporter(name))

    # Get parameters with defaults
    parameters = context.params
    min_n = parameters.get(PARAM_MIN_N, 3)
    max_n = parameters.get(PARAM_MAX_N, 5)

    # Configure tokenizer for social media text processing
    tokenizer_config = TokenizerConfig(
        case_handling=CaseHandling.LOWERCASE,
        normalize_unicode=True,
        extract_hashtags=True,
        extract_mentions=True,
        include_urls=True,
        min_token_length=1,
    )

    input_reader = context.input()
    df_input = input_reader.preprocess(pl.read_parquet(input_reader.parquet_path))
    with progress("Preprocessing messages"):
        df_input = _preprocess_messages(df_input)

    with progress("Detecting n-grams") as reporter:
        df_ngram_instances, df_ngram_defs = _extract_ngrams_from_messages(
            df_input,
            min_n,
            max_n,
            tokenizer_config,
            reporter.update,
            spill_dir=context.temp_dir,
        )

    with progress("Fetching n-gram statistics"):
        (
            df_ngram_instances.sort(
                by=[COL_MESSAGE_SURROGATE_ID, COL_NGRAM_ID]
            ).write_parquet(context.output(OUTPUT_MESSAGE_NGRAMS).parquet_path)
        )

    with progress("Outputting n-gram definitions"):
        df_ngram_defs.write_parquet(context.output(OUTPUT_NGRAM_DEFS).parquet_path)

    with progress("Outputting messages"):
        (
            df_input.select(
                [
                    COL_MESSAGE_SURROGATE_ID,
                    COL_MESSAGE_ID,
                    COL_MESSAGE_TEXT,
                    COL_AUTHOR_ID,
                    COL_MESSAGE_TIMESTAMP,
                ]
            ).write_parquet(context.output(OUTPUT_MESSAGE).parquet_path)
        )


def ngrams(tokens: list[str], min: int, max: int):
    """Generate n-grams from list of tokens."""
    for i in range(len(tokens) - min + 1):
        for n in range(min, max + 1):
            if i + n > len(tokens):
                break
            yield tokens[i : i + n]


def serialize_ngram(ngram: list[str]) -> str:
    """Generates a string that uniquely represents an ngram"""
    return " ".join(ngram)
