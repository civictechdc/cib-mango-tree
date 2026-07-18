import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from math import ceil

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


def _emit_ngram_pairs(
    payload: tuple[list[int], list[str], int, int, TokenizerConfig],
) -> pl.DataFrame:
    """
    Tokenize a chunk of messages and emit one row per (message, distinct n-gram).

    Intended to be dispatched to worker processes, and thus only takes picklable
    arguments. It does not assign n-gram ids at this stage, in order to avoid
    a cross-chunk counter.

    Args:
        payload: (surrogate_ids, texts, min_n, max_n, tokenizer_config)

    Returns:
        DataFrame with columns [message_surrogate_id, words]
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

    return pl.DataFrame(
        {
            COL_MESSAGE_SURROGATE_ID: pl.Series(out_surrogate_ids, dtype=pl.Int64),
            COL_NGRAM_WORDS: pl.Series(out_words, dtype=pl.String),
        }
    )


def _run_chunks(
    payloads: list[tuple], max_workers: int, progress_callback=None
) -> list[pl.DataFrame]:
    """Run _emit_ngram_pairs over payloads, in worker processes when worthwhile."""
    total = len(payloads)

    if max_workers <= 1:
        frames = []
        for done, payload in enumerate(payloads, start=1):
            frames.append(_emit_ngram_pairs(payload))
            if progress_callback:
                progress_callback(done / total)
        return frames
    else:
        results: dict[int, pl.DataFrame] = {}
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_emit_ngram_pairs, payload): index
                for index, payload in enumerate(payloads)
            }
            for done, future in enumerate(as_completed(futures), start=1):
                results[futures[future]] = future.result()
                if progress_callback:
                    progress_callback(done / total)

        # Reassemble in submission order so the output does not depend on completion order.
        return [results[index] for index in range(total)]


def _extract_ngrams_from_messages(
    df_input: pl.DataFrame,
    min_n: int,
    max_n: int,
    tokenizer_config: TokenizerConfig,
    progress_callback=None,
    max_workers: int | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Extract n-grams from messages with within-message deduplication.

    N-grams occurring in only one message are dropped immediately. These make up
    the great majority of distinct n-grams on a typical corpus.

    Args:
        df_input: Preprocessed dataframe with messages
        min_n: Minimum n-gram length
        max_n: Maximum n-gram length
        tokenizer_config: Configuration for text tokenization
        progress_callback: Optional callback for progress reporting
        max_workers: Worker processes to use. Defaults to one per available core.

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

    frames = _run_chunks(payloads, max_workers, progress_callback)
    df_pairs = pl.concat(frames) if frames else _empty_pairs_frame()

    # Sorting before assigning ids keeps ngram_id stable across runs: group_by output
    # order is not deterministic, and the ids feed the sort order of the outputs.
    df_ngram_defs = (
        df_pairs.group_by(COL_NGRAM_WORDS)
        .len()
        .filter(pl.col("len") > 1)
        .select(COL_NGRAM_WORDS)
        .sort(COL_NGRAM_WORDS)
        .with_row_index(COL_NGRAM_ID)
        .with_columns(
            pl.col(COL_NGRAM_ID).cast(pl.Int64),
            pl.col(COL_NGRAM_WORDS).str.split(" ").list.len().alias(COL_NGRAM_LENGTH),
        )
    )

    df_message_ngrams = df_pairs.join(
        df_ngram_defs.select(COL_NGRAM_WORDS, COL_NGRAM_ID),
        on=COL_NGRAM_WORDS,
        how="inner",
    ).select(COL_MESSAGE_SURROGATE_ID, COL_NGRAM_ID)

    return df_message_ngrams, df_ngram_defs


def _empty_pairs_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            COL_MESSAGE_SURROGATE_ID: pl.Series([], dtype=pl.Int64),
            COL_NGRAM_WORDS: pl.Series([], dtype=pl.String),
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
            df_input, min_n, max_n, tokenizer_config, reporter.update
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
