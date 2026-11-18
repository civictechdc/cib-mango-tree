"""Behavior tests for export worker progress messaging."""

from __future__ import annotations

import queue
from pathlib import Path
from unittest.mock import MagicMock

from cibmangotree.gui.components.export_outputs import (
    ExportProgressMessage,
    _count_chunks,
    _export_worker,
)


def test_count_chunks_for_single_and_globbed_paths(tmp_path: Path) -> None:
    assert _count_chunks(str(tmp_path / "out.csv")) == 1

    (tmp_path / "out_0.csv").write_text("a\n1\n", encoding="utf-8")
    (tmp_path / "out_1.csv").write_text("a\n2\n", encoding="utf-8")
    assert _count_chunks(str(tmp_path / "out_[*].csv")) == 2


def test_export_worker_reports_success_and_completion(tmp_path: Path) -> None:
    exported = tmp_path / "summary.csv"
    exported.write_text("Count,Label\n1,x\n", encoding="utf-8")

    def _successful_export(*, format: str):
        assert format == "csv"
        if False:
            yield 0.0
        return str(exported)

    output = MagicMock()
    output.descriptive_qualified_name = "Summary (Base)"
    output.export.side_effect = lambda **kwargs: _successful_export(**kwargs)

    progress: queue.Queue = queue.Queue()
    _export_worker([output], "csv", progress)

    messages = []
    while not progress.empty():
        messages.append(progress.get_nowait())

    assert [msg.msg_type for msg in messages] == [
        "output_start",
        "output_finish",
        "all_complete",
    ]
    finish = messages[1]
    assert isinstance(finish, ExportProgressMessage)
    assert finish.name == "Summary (Base)"
    assert finish.path == str(exported)
    assert finish.chunk_count == 1


def test_export_worker_reports_errors_and_still_completes() -> None:
    def _failing_export(*, format: str):
        raise RuntimeError("disk full")
        yield  # pragma: no cover

    output = MagicMock()
    output.descriptive_qualified_name = "Broken (Base)"
    output.export.side_effect = lambda **kwargs: _failing_export(**kwargs)

    progress: queue.Queue = queue.Queue()
    _export_worker([output], "json", progress)

    messages = []
    while not progress.empty():
        messages.append(progress.get_nowait())

    assert [msg.msg_type for msg in messages] == [
        "output_start",
        "output_error",
        "all_complete",
    ]
    assert messages[1].error == "disk full"
