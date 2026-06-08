import glob
import os
import queue
import threading
from typing import Literal

from nicegui import run, ui
from pydantic import BaseModel, Field

from cibmangotree.app import AnalysisContext, AnalysisOutputContext
from cibmangotree.gui.theme import MANGO_DARK_GREEN
from cibmangotree.gui.utils import open_directory_explorer
from cibmangotree.storage import SupportedOutputExtension

QUEUE_POLL_INTERVAL = 0.5
LARGE_OUTPUT_THRESHOLD = 100_000


class ExportProgressMessage(BaseModel):
    msg_type: Literal[
        "output_start",
        "output_progress",
        "output_finish",
        "output_error",
        "all_complete",
    ] = Field(...)
    name: str | None = None
    index: int | None = None
    total: int | None = None
    chunk_progress: float | None = None
    path: str | None = None
    chunk_count: int | None = None
    error: str | None = None


def _count_chunks(path_pattern: str) -> int:
    """Count the number of chunk files matching a glob pattern."""
    if "[*]" not in path_pattern:
        return 1
    return len(glob.glob(path_pattern.replace("[*]", "*")))


def _export_worker(
    outputs: list[AnalysisOutputContext],
    format: SupportedOutputExtension,
    progress_queue: queue.Queue,
):
    """Run the export in a background thread, sending progress messages to the queue."""
    total = len(outputs)
    for i, output in enumerate(outputs):
        progress_queue.put(
            ExportProgressMessage(
                msg_type="output_start",
                name=output.descriptive_qualified_name,
                index=i,
                total=total,
            )
        )

        gen = output.export(format=format)
        try:
            while True:
                chunk_progress = next(gen)
                progress_queue.put(
                    ExportProgressMessage(
                        msg_type="output_progress",
                        name=output.descriptive_qualified_name,
                        index=i,
                        total=total,
                        chunk_progress=chunk_progress,
                    )
                )
        except StopIteration as e:
            path = e.value
            chunk_count = _count_chunks(path)
            progress_queue.put(
                ExportProgressMessage(
                    msg_type="output_finish",
                    name=output.descriptive_qualified_name,
                    index=i,
                    total=total,
                    path=path,
                    chunk_count=chunk_count,
                )
            )
        except Exception as exc:
            progress_queue.put(
                ExportProgressMessage(
                    msg_type="output_error",
                    name=output.descriptive_qualified_name,
                    index=i,
                    total=total,
                    error=str(exc),
                )
            )

    progress_queue.put(ExportProgressMessage(msg_type="all_complete"))


class ExportDialog(ui.dialog):
    """Multi-step dialog for selecting and exporting analysis outputs."""

    def __init__(self, analysis_context: AnalysisContext):
        super().__init__()

        self.analysis_context = analysis_context

        self.outputs = sorted(
            analysis_context.get_all_exportable_outputs(),
            key=lambda output: (
                (
                    "0"
                    if output.secondary_spec is None
                    else "1_" + output.secondary_spec.name
                ),
                output.descriptive_qualified_name,
            ),
        )

        self.selected_outputs: list[AnalysisOutputContext] = []
        self.format: SupportedOutputExtension | None = None
        self.exported_paths: list[tuple[str, int]] = []
        self.export_errors: list[str] = []

        self.progress_queue: queue.Queue | None = None
        self.timer: ui.timer | None = None

        self.output_status_rows: dict[str, tuple] = {}

        with (
            self,
            ui.card().classes("w-full").style("min-width: 500px; max-width: 700px"),
        ):
            self._build_select_outputs()
            self._build_configure_export()
            self._build_export_progress()
            self._build_export_complete()

        self._show_step("select_outputs")

    def _show_step(self, step: str):
        steps = {
            "select_outputs": self.select_outputs,
            "configure_export": self.configure_export,
            "export_progress": self.export_progress,
            "export_complete": self.export_complete,
        }
        for name, card in steps.items():
            card.set_visibility(name == step)

    def _add_checkbox_group(
        self, label_text: str, outputs: list[AnalysisOutputContext]
    ):
        ui.label(label_text).classes("text-subtitle2 text-weight-bold q-mt-sm")
        ui.separator()
        for output in outputs:
            cb = ui.checkbox(
                f"{output.descriptive_qualified_name}",
                on_change=lambda _=None: self._on_selection_changed(),
            )
            self.output_checkboxes.append((output, cb))

    def _build_select_outputs(self):
        self.select_outputs = ui.column().classes("w-full")
        with self.select_outputs:
            ui.label("Select outputs to export").classes("text-h6 q-mb-md")

            self.output_checkboxes: list[tuple[AnalysisOutputContext, ui.checkbox]] = []
            self.checkbox_container = ui.column().classes("w-full gap-1 mb-4")

            with self.checkbox_container:
                primary_outputs = [o for o in self.outputs if o.secondary_spec is None]
                secondary_outputs = [
                    o for o in self.outputs if o.secondary_spec is not None
                ]

                if primary_outputs:
                    self._add_checkbox_group("Primary Outputs", primary_outputs)

                if secondary_outputs:
                    sec_names = sorted(
                        {o.secondary_spec.name for o in secondary_outputs}
                    )
                    for sec_name in sec_names:
                        sec_outputs = [
                            o
                            for o in secondary_outputs
                            if o.secondary_spec.name == sec_name
                        ]
                        self._add_checkbox_group("Secondary Outputs", sec_outputs)

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=self.close, color="secondary")
                self.select_outputs_next = ui.button(
                    "Next",
                    on_click=self._go_to_configure_export,
                    color="primary",
                    icon="arrow_forward",
                )
                self.select_outputs_next.set_enabled(False)

    def _on_selection_changed(self):
        has_selection = any(cb.value for _, cb in self.output_checkboxes)
        self.select_outputs_next.set_enabled(has_selection)

    def _go_to_configure_export(self):
        self.selected_outputs = [
            output for output, cb in self.output_checkboxes if cb.value
        ]

        self.chunking_visible = any(
            output.num_rows > LARGE_OUTPUT_THRESHOLD for output in self.selected_outputs
        )
        self.chunking_section.set_visibility(self.chunking_visible)
        self._show_step("configure_export")

    def _build_configure_export(self):
        self.configure_export = ui.column().classes("w-full")
        with self.configure_export:
            ui.label("Configure export").classes("text-h6 q-mb-md")

            is_hashtags = self.analysis_context.analyzer_id == "hashtags"
            format_options: dict[str, str] = {}
            if not is_hashtags:
                format_options["csv"] = "CSV"
                format_options["xlsx"] = "Excel"
            format_options["json"] = "JSON"

            self.format_toggle = ui.toggle(
                format_options,
                value=list(format_options.keys())[0],
            ).classes("q-mb-md")

            self.chunking_visible = False
            self.chunking_section = ui.column().classes("w-full")
            self.chunking_section.set_visibility(False)
            with self.chunking_section:
                ui.label("Chunking options").classes(
                    "text-subtitle2 text-weight-bold q-mt-sm"
                )
                ui.label(
                    f"Control how outputs larger than "
                    f"{LARGE_OUTPUT_THRESHOLD:,} rows are saved."
                ).classes("q-mb-md text-sm")

                settings = self.analysis_context.app_context.settings
                current_chunk = settings.export_chunk_size
                is_current_chunking = (
                    current_chunk is not None and current_chunk is not False
                )
                default_toggle = (
                    is_current_chunking if current_chunk is not None else True
                )

                self.chunk_toggle = ui.toggle(
                    {True: "Break into chunks", False: "Export in a single file"},
                    value=default_toggle,
                ).classes("q-mb-md")

                self.chunk_size_input = ui.number(
                    "Rows per chunk",
                    value=(
                        current_chunk
                        if isinstance(current_chunk, int)
                        else LARGE_OUTPUT_THRESHOLD
                    ),
                    min=100,
                ).classes("q-mb-md")

                if not is_current_chunking:
                    self.chunk_size_input.set_visibility(False)

                self.chunk_toggle.on_value_change(
                    lambda: self.chunk_size_input.set_visibility(
                        self.chunk_toggle.value
                    )
                )

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button(
                    "Back",
                    on_click=lambda: self._show_step("select_outputs"),
                    color="secondary",
                    icon="arrow_back",
                )
                ui.button(
                    "Start Export",
                    on_click=self._handle_start_export,
                    color="primary",
                    icon="arrow_forward",
                )

    def _handle_start_export(self):
        self.format = self.format_toggle.value

        if self.chunking_visible:
            settings = self.analysis_context.app_context.settings
            if self.chunk_toggle.value:
                settings.set_export_chunk_size(self.chunk_size_input.value)
            else:
                settings.set_export_chunk_size(False)

        self._start_export()

    def _build_export_progress(self):
        self.export_progress = ui.column().classes("w-full")
        with self.export_progress:
            ui.label("Exporting...").classes("text-h6 q-mb-md")

            self.export_status_label = ui.label("Preparing...").classes(
                "text-base q-mb-md"
            )

            self.export_progress_bar = (
                ui.linear_progress(value=0, show_value=False)
                .classes("w-full q-mb-md")
                .props("instant-feedback")
            )

            self.output_status_container = ui.column().classes("w-full gap-1 mb-4")

    def _build_export_complete(self):
        self.export_complete = ui.column().classes("w-full")
        with self.export_complete:
            with ui.row().classes("items-center gap-2 q-mb-md"):
                self.complete_success_icon = ui.icon(
                    "check_circle", color=MANGO_DARK_GREEN, size="lg"
                )
                self.complete_error_icon = ui.icon(
                    "cancel", color="negative", size="lg"
                )
                self.complete_status_label = ui.label("").classes("text-h6")
                self.complete_success_icon.set_visibility(False)
                self.complete_error_icon.set_visibility(False)

            self.complete_message_container = ui.column().classes("w-full gap-1 mb-4")

            with ui.row().classes("w-full justify-end gap-2"):
                self.export_complete_open_folder = ui.button(
                    "Open exports folder",
                    on_click=self._open_folder,
                    color="primary",
                    icon="folder_open",
                )
                ui.button("Close", on_click=self.close, color="secondary")

    def _start_export(self):
        if self.format is None:
            ui.notify("Please select an export format", type="warning")
            self._show_step("configure_export")
            return

        self._show_step("export_progress")

        self.progress_queue = queue.Queue()
        self.exported_paths = []
        self.export_errors = []
        self.output_status_rows.clear()

        self.output_status_container.clear()

        self.export_progress_bar.value = 0

        thread = threading.Thread(
            target=_export_worker,
            args=(
                self.selected_outputs,
                self.format,
                self.progress_queue,
            ),
            daemon=True,
        )
        thread.start()

        self.timer = ui.timer(QUEUE_POLL_INTERVAL, self._poll_progress)

    def _poll_progress(self):
        try:
            msg = self.progress_queue.get_nowait()
        except queue.Empty:
            return

        if msg.msg_type == "output_start":
            self.export_status_label.text = f"Exporting {msg.name}..."
            self.export_progress_bar.value = msg.index / msg.total

            with self.output_status_container:
                with ui.row().classes("items-center gap-2") as row:
                    spinner = ui.spinner("gears", size="sm")
                    label = ui.label(msg.name).classes("text-sm")
                self.output_status_rows[msg.name] = (row, spinner, label)

        elif msg.msg_type == "output_progress":
            self.export_progress_bar.value = (
                msg.index + msg.chunk_progress
            ) / msg.total
            if msg.name in self.output_status_rows:
                _, _, label = self.output_status_rows[msg.name]
                label.text = f"{msg.name} ({msg.chunk_progress * 100:.0f}%)"

        elif msg.msg_type == "output_finish":
            self.export_progress_bar.value = (msg.index + 1) / msg.total
            self.exported_paths.append((msg.path, msg.chunk_count))
            if msg.name in self.output_status_rows:
                _, spinner, label = self.output_status_rows[msg.name]
                spinner.set_visibility(False)
                if msg.chunk_count > 1:
                    display_path = msg.path.replace("_[*]", "")
                    label.text = (
                        f"Exported as {os.path.basename(display_path)} "
                        f"in {msg.chunk_count} chunks"
                    )
                else:
                    label.text = f"Exported as {os.path.basename(msg.path)}"

        elif msg.msg_type == "output_error":
            self.export_errors.append(f"{msg.name}: {msg.error}")
            if msg.name in self.output_status_rows:
                _, spinner, label = self.output_status_rows[msg.name]
                spinner.set_visibility(False)
                label.text = f"Error: {msg.name} \u2014 {msg.error}"

        elif msg.msg_type == "all_complete":
            self._on_export_complete()

    def _on_export_complete(self):
        if self.timer:
            self.timer.cancel()
            self.timer = None

        self.export_progress_bar.value = 1.0
        if self.export_errors:
            self.complete_status_label.text = "Export completed with errors"
            self.complete_error_icon.set_visibility(True)
            self.complete_success_icon.set_visibility(False)
        else:
            self.complete_status_label.text = "Export complete!"
            self.complete_success_icon.set_visibility(True)
            self.complete_error_icon.set_visibility(False)

        self.complete_message_container.clear()
        with self.complete_message_container:
            if self.exported_paths:
                for path, chunk_count in self.exported_paths:
                    if chunk_count > 1:
                        display_path = path.replace("_[*]", "")
                        ui.label(
                            f"Exported {os.path.basename(display_path)} in {chunk_count} chunks"
                        ).classes("text-sm")
                    else:
                        ui.label(f"Exported {os.path.basename(path)}").classes(
                            "text-sm"
                        )

            if self.export_errors:
                for error in self.export_errors:
                    ui.label(error).classes("text-sm")

        self.export_complete_open_folder.set_visibility(bool(self.exported_paths))
        self._show_step("export_complete")

    async def _open_folder(self):
        await run.io_bound(
            open_directory_explorer, self.analysis_context.export_root_path
        )
