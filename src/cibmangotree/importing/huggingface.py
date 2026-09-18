import warnings
from urllib.parse import urlparse

import polars as pl
from huggingface_hub import HfApi
from huggingface_hub import hf_hub_download as _hf_hub_download
from pydantic import BaseModel

from .importer import Importer, ImporterSession

# Data file extensions we know how to parse once downloaded, in the order we
# prefer to auto-select them when a dataset repo has more than one candidate.
SUPPORTED_EXTENSIONS = (".parquet", ".csv", ".tsv", ".jsonl", ".json")


def parse_dataset_repo_id(source: str) -> str | None:
    """
    Extract a `namespace/name` Hugging Face dataset repo id from a dataset page
    URL (e.g. https://huggingface.co/datasets/namespace/name[/...]), or return
    the input unchanged if it already looks like a bare repo id.
    """
    value = source.strip()
    if not value:
        return None

    if value.startswith(("http://", "https://")):
        parsed = urlparse(value)
        if not parsed.netloc.endswith("huggingface.co"):
            return None
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 3 or parts[0] != "datasets":
            return None
        return f"{parts[1]}/{parts[2]}"

    parts = [part for part in value.split("/") if part]
    if len(parts) == 2:
        return "/".join(parts)

    return None


def _list_data_files(repo_id: str) -> list[str]:
    # Let network/auth/not-found errors from the Hub propagate: the caller
    # surfaces them instead of silently treating them as "not importable".
    files = HfApi().list_repo_files(repo_id, repo_type="dataset")
    return sorted(f for f in files if f.lower().endswith(SUPPORTED_EXTENSIONS))


def _download(repo_id: str, filename: str) -> str:
    # Hugging Face Hub warns on machines that can't create symlinks (e.g.
    # Windows without dev mode). Caching still works, so this is just noise.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", category=UserWarning, module="huggingface_hub"
        )
        return _hf_hub_download(repo_id=repo_id, filename=filename, repo_type="dataset")


class HuggingFaceImporter(Importer["HuggingFaceImportSession"]):
    """
    Importer that resolves a Hugging Face dataset URL or `namespace/name` repo
    id to one of its data files (CSV/TSV/JSON/JSONL/Parquet), to be downloaded
    and converted to Parquet by the resulting `HuggingFaceImportSession`.
    """

    @property
    def name(self) -> str:
        return "Hugging Face dataset"

    def suggest(self, input_path: str) -> bool:
        return parse_dataset_repo_id(input_path) is not None

    def init_session(self, input_path: str) -> "HuggingFaceImportSession | None":
        """
        For a repo with exactly one supported data file, builds a session for
        it directly. For a repo with zero or multiple candidate files, returns
        None - the caller is responsible for listing files (`list_data_files`)
        and letting the user pick one to build a session from directly.
        """
        repo_id = parse_dataset_repo_id(input_path)
        if repo_id is None:
            return None

        data_files = _list_data_files(repo_id)
        if len(data_files) != 1:
            return None

        return HuggingFaceImportSession(repo_id=repo_id, filename=data_files[0])

    @staticmethod
    def list_data_files(input_path: str) -> list[str]:
        """
        List the importable data files in the dataset repo referenced by
        `input_path`, for a caller (e.g. a GUI) to present as choices when
        `init_session` returns None due to ambiguity. Returns an empty list
        if `input_path` isn't a recognizable dataset URL/repo id.
        """
        repo_id = parse_dataset_repo_id(input_path)
        if repo_id is None:
            return []
        return _list_data_files(repo_id)


class HuggingFaceImportSession(ImporterSession, BaseModel):
    """
    Configuration for importing a single file out of a Hugging Face dataset
    repo. Downloading is deferred until `load_preview`/`import_as_parquet` are
    called, and is cached on disk by `huggingface_hub` between the two.
    """

    repo_id: str
    filename: str

    def load_preview(self, n_records: int) -> pl.DataFrame | None:
        local_path = _download(self.repo_id, self.filename)
        return _read_data_file(local_path, self.filename, n_rows=n_records)

    def import_as_parquet(self, output_path: str) -> None:
        local_path = _download(self.repo_id, self.filename)
        df = _read_data_file(local_path, self.filename, n_rows=None)
        df.write_parquet(output_path)


def _read_data_file(
    local_path: str, filename: str, *, n_rows: int | None
) -> pl.DataFrame:
    lower = filename.lower()

    if lower.endswith(".parquet"):
        return pl.read_parquet(local_path, n_rows=n_rows)

    if lower.endswith(".tsv"):
        return pl.read_csv(
            local_path,
            separator="\t",
            n_rows=n_rows,
            truncate_ragged_lines=True,
            ignore_errors=True,
        )

    if lower.endswith(".jsonl"):
        return pl.read_ndjson(local_path, n_rows=n_rows)

    if lower.endswith(".json"):
        # A plain JSON file is a single array, so it can't be read partially.
        df = pl.read_json(local_path)
        return df.head(n_rows) if n_rows is not None else df

    return pl.read_csv(
        local_path, n_rows=n_rows, truncate_ragged_lines=True, ignore_errors=True
    )
