from pathlib import Path
from unittest.mock import patch

import polars as pl

from .huggingface import (
    HuggingFaceImporter,
    HuggingFaceImportSession,
    parse_dataset_repo_id,
)


class TestParseDatasetRepoId:
    def test_dataset_url(self):
        assert (
            parse_dataset_repo_id("https://huggingface.co/datasets/stanfordnlp/imdb")
            == "stanfordnlp/imdb"
        )

    def test_dataset_url_with_trailing_path(self):
        url = "https://huggingface.co/datasets/stanfordnlp/imdb/viewer/plain_text"
        assert parse_dataset_repo_id(url) == "stanfordnlp/imdb"

    def test_bare_repo_id(self):
        assert parse_dataset_repo_id("stanfordnlp/imdb") == "stanfordnlp/imdb"

    def test_non_dataset_url_rejected(self):
        assert parse_dataset_repo_id("https://huggingface.co/stanfordnlp/imdb") is None

    def test_non_huggingface_url_rejected(self):
        assert parse_dataset_repo_id("https://example.com/datasets/foo/bar") is None

    def test_blank_input_rejected(self):
        assert parse_dataset_repo_id("") is None
        assert parse_dataset_repo_id("   ") is None

    def test_malformed_repo_id_rejected(self):
        assert parse_dataset_repo_id("just-a-name") is None
        assert parse_dataset_repo_id("a/b/c") is None


class TestHuggingFaceImporter:
    def setup_method(self):
        self.importer = HuggingFaceImporter()

    def test_suggest_true_for_dataset_url(self):
        assert self.importer.suggest("https://huggingface.co/datasets/foo/bar")

    def test_suggest_false_for_local_path(self):
        assert not self.importer.suggest("/some/local/file.csv")

    @patch("cibmangotree.importing.huggingface.HfApi")
    def test_init_session_auto_selects_single_file(self, mock_hf_api):
        mock_hf_api.return_value.list_repo_files.return_value = [
            "README.md",
            "data/train.parquet",
        ]

        session = self.importer.init_session("foo/bar")

        assert session == HuggingFaceImportSession(
            repo_id="foo/bar", filename="data/train.parquet"
        )

    @patch("cibmangotree.importing.huggingface.HfApi")
    def test_init_session_returns_none_with_no_data_files(self, mock_hf_api):
        mock_hf_api.return_value.list_repo_files.return_value = ["README.md"]

        assert self.importer.init_session("foo/bar") is None

    @patch("cibmangotree.importing.huggingface.HfApi")
    def test_init_session_returns_none_with_multiple_data_files(self, mock_hf_api):
        mock_hf_api.return_value.list_repo_files.return_value = [
            "train.csv",
            "test.csv",
        ]

        assert self.importer.init_session("foo/bar") is None

    @patch("cibmangotree.importing.huggingface.HfApi")
    def test_init_session_returns_none_for_invalid_source(self, mock_hf_api):
        assert self.importer.init_session("not-a-repo-id") is None
        mock_hf_api.return_value.list_repo_files.assert_not_called()

    @patch("cibmangotree.importing.huggingface.HfApi")
    def test_list_data_files_returns_matching_files(self, mock_hf_api):
        mock_hf_api.return_value.list_repo_files.return_value = [
            "README.md",
            "train.csv",
            "test.csv",
        ]

        assert HuggingFaceImporter.list_data_files("foo/bar") == [
            "test.csv",
            "train.csv",
        ]

    def test_list_data_files_returns_empty_for_invalid_source(self):
        assert HuggingFaceImporter.list_data_files("not-a-repo-id") == []


class TestHuggingFaceImportSession:
    def test_import_as_parquet(self, tmp_path: Path):
        session = HuggingFaceImportSession(repo_id="foo/bar", filename="data.csv")

        source_csv = tmp_path / "data.csv"
        source_csv.write_text("a,b\n1,2\n3,4\n")
        output_path = str(tmp_path / "out.parquet")

        with patch(
            "cibmangotree.importing.huggingface._download", return_value=str(source_csv)
        ) as mock_download:
            session.import_as_parquet(output_path)

        mock_download.assert_called_once_with("foo/bar", "data.csv")
        assert pl.read_parquet(output_path).to_dicts() == [
            {"a": 1, "b": 2},
            {"a": 3, "b": 4},
        ]

    def test_load_preview_respects_n_records(self, tmp_path: Path):
        session = HuggingFaceImportSession(repo_id="foo/bar", filename="data.csv")

        source_csv = tmp_path / "data.csv"
        source_csv.write_text("a,b\n1,2\n3,4\n5,6\n")

        with patch(
            "cibmangotree.importing.huggingface._download", return_value=str(source_csv)
        ):
            preview = session.load_preview(2)

        assert len(preview) == 2
