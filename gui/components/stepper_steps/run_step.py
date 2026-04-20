from asyncio import sleep
from multiprocessing import Manager
from queue import Empty
from traceback import format_exc

from nicegui import run, ui

from app.analysis_context import AnalysisContext, AnalysisQueueMessage
from gui.routes import gui_routes
from gui.session import GuiSession
from gui.theme import MANGO_DARK_GREEN, MANGO_ORANGE

QUEUE_POLL_INTERVAL = 0.05


class RunAnalysisStep:
    """Step 4: Execute the analysis with progress tracking."""

    def __init__(
        self,
        session: GuiSession,
        notify_success,
        notify_warning,
        notify_error,
        navigate_to,
    ):
        self.session = session
        self.notify_success = notify_success
        self.notify_warning = notify_warning
        self.notify_error = notify_error
        self.navigate_to = navigate_to

    @ui.refreshable_method
    def render(self) -> None:
        """Render the run analysis button and summary."""
        analyzer = self.session.selected_analyzer
        column_mapping = self.session.column_mapping
        params = self.session.analysis_params

        if not analyzer:
            ui.label("Please select an analyzer first").classes("text-grey")
            return

        if not column_mapping:
            ui.label("Please map columns first").classes("text-grey")
            return

        with (
            ui.column()
            .classes("w-full items-center gap-6")
            .style("max-width: 960px; margin: 0 auto;")
        ):
            ui.label("Configuration Summary").classes("text-lg font-bold mb-4")

            with ui.card().classes("w-full p-4 no-shadow border border-gray-200"):
                with ui.column().classes("gap-2"):
                    ui.label(
                        f"Analyzer: {analyzer.name if analyzer else 'Not selected'}"
                    ).classes("text-sm")
                    ui.label(
                        f"Columns: {len(column_mapping) if column_mapping else 0} mapped"
                    ).classes("text-sm")
                    ui.label(
                        f"Parameters: {len(params) if params else 0} configured"
                    ).classes("text-sm")

            ui.button(
                "Run Analysis",
                icon="play_arrow",
                color="primary",
                on_click=self._start_analysis,
            ).classes("text-base")

    def is_valid(self) -> bool:
        """Check if all prerequisites are configured."""
        return (
            self.session.selected_analyzer is not None
            and self.session.column_mapping is not None
            and self.session.analysis_params is not None
        )

    async def _start_analysis(self) -> None:
        """Opens dialog and runs the analysis in a separate process."""
        analyzer = self.session.selected_analyzer
        project = self.session.current_project

        if not analyzer or not project:
            self.notify_error("Missing analyzer or project")
            return

        try:
            analysis = project.create_analysis(
                analyzer.id,
                self.session.column_mapping,
                self.session.analysis_params,
            )
        except Exception as e:
            self.notify_error(f"Failed to create analysis: {str(e)}")
            print(f"Analysis creation error:\n{format_exc()}")
            return

        secondary_analyzers = (
            self.session.app.context.suite.find_toposorted_secondary_analyzers(analyzer)
        )
        secondary_analyzer_ids = [sec.id for sec in secondary_analyzers]

        manager = Manager()
        queue = manager.Queue()
        cancel_event = manager.Event()

        input_columns_data = {
            analyzer_col_name: (
                user_col_name,
                project.column_dict[user_col_name].semantic.semantic_name,
            )
            for analyzer_col_name, user_col_name in analysis.column_mapping.items()
        }

        with (
            ui.dialog().props("persistent") as dialog,
            ui.card()
            .classes("items-center justify-center gap-6")
            .style("width: 600px; max-width: 90vw; padding: 2rem;"),
        ):
            analyzer_header = ui.label(analyzer.name).classes("text-xl font-semibold")
            status_label = (
                ui.label("Initializing...")
                .classes("text-base text-medium")
                .style(f"color: {MANGO_ORANGE}")
            )

            step_list_container = ui.column().classes("w-full gap-1 mt-4")

            log_container = ui.column().classes("w-full gap-1 mt-2")

            with ui.row().classes("gap-4 mt-4"):
                cancel_btn = ui.button(
                    "Cancel Analysis",
                    icon="stop",
                    color="secondary",
                    on_click=lambda: cancel_event.set(),
                ).props("outline")

                success_btn = ui.button(
                    "Continue",
                    icon="arrow_forward",
                    color="primary",
                    on_click=lambda: (
                        dialog.close(),
                        self.navigate_to(gui_routes.post_analysis),
                    ),
                )
                success_btn.set_visibility(False)

        analysis_complete = False
        step_rows: dict[str, tuple[ui.spinner, ui.icon, ui.label]] = {}
        current_step_name: str = None

        def _poll_queue():
            nonlocal analysis_complete, current_step_name

            try:
                msg_dict = queue.get_nowait()
            except Empty:
                return

            msg = AnalysisQueueMessage(**msg_dict)

            if msg.type == "analyzer_start":
                analyzer_header.text = msg.analyzer_name or "Analyzer"
                status_label.text = "Analysis starting..."
                step_rows.clear()
                current_step_name = None

            elif msg.type == "analyzer_finish":
                pass

            elif msg.type == "step_start":
                step_name = msg.step_name or "Processing..."

                if current_step_name and current_step_name in step_rows:
                    _, _, prev_label = step_rows[current_step_name]
                    prev_label.classes(add="text-gray-600", remove="text-medium")
                    prev_label.style("")

                current_step_name = step_name
                status_label.text = "Running analysis..."

                with step_list_container:
                    with ui.row().classes("items-center gap-2"):
                        spinner = ui.spinner("gears", size="sm")
                        checkmark = ui.icon(
                            "check_circle", color=MANGO_DARK_GREEN, size="sm"
                        )
                        checkmark.set_visibility(False)
                        label = ui.label(step_name).classes("text-medium")
                step_rows[step_name] = (spinner, checkmark, label)

            elif msg.type == "step_finish":
                if current_step_name and current_step_name in step_rows:
                    spinner, checkmark, label = step_rows[current_step_name]
                    spinner.set_visibility(False)
                    checkmark.set_visibility(True)
                    label.classes(add="text-gray-600", remove="text-medium")
                    label.style("")
                    label.text = current_step_name
                current_step_name = None

            elif msg.type == "step_progress":
                if current_step_name and current_step_name in step_rows:
                    _, _, label = step_rows[current_step_name]
                    progress_pct = (msg.step_progress or 0) * 100
                    label.text = f"{current_step_name} ({progress_pct:.0f}%)"

            elif msg.type == "log":
                with log_container:
                    label = ui.label(msg.message).classes("text-sm")
                    if msg.progress is not None:
                        label.text = f"{msg.message} ({msg.progress * 100:.0f}%)"

            elif msg.type == "error":
                with log_container:
                    ui.label(f"Error: {msg.message}").classes(
                        "text-negative font-bold text-sm"
                    )
                cancel_btn.disable()
                analysis_complete = True

            elif msg.type in ("complete", "cancelled"):
                analysis_complete = True
                status_label.set_visibility(False)
                if msg.type == "complete":
                    self.session.current_analysis = analysis.model
                    success_btn.set_visibility(True)
                    self.notify_success("Analysis completed!")
                else:
                    self.notify_warning("Analysis was canceled")
                cancel_btn.disable()

        async def run_analysis_task():
            try:
                result = await run.cpu_bound(
                    AnalysisContext.run_worker,
                    analysis.model,
                    analyzer.id,
                    analysis.column_mapping,
                    input_columns_data,
                    secondary_analyzer_ids,
                    analysis.app_context.storage,
                    queue,
                    cancel_event,
                )
                analysis.model.is_draft = result.is_draft
            except Exception as e:
                self.notify_error(f"Analysis error: {str(e)}")
                print(f"Analysis error:\n{format_exc()}")
                with log_container:
                    ui.label(f"Error: {str(e)}").classes(
                        "text-negative font-bold text-sm"
                    )
                cancel_btn.disable()
            finally:
                if analysis.is_draft:
                    analysis.delete()

        dialog.open()
        timer = ui.timer(QUEUE_POLL_INTERVAL, _poll_queue)

        await run_analysis_task()

        while not analysis_complete:
            await sleep(QUEUE_POLL_INTERVAL)

        timer.cancel()
