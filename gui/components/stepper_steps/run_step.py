from asyncio import sleep
from multiprocessing import Event, Manager
from queue import Empty
from traceback import format_exc

from nicegui import run, ui

from app.analysis_context import AnalysisContext, AnalysisQueueMessage
from gui.base import GuiSession, gui_routes

UI_RENDER_DELAY = 0.1
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
        total_steps = 1 + len(secondary_analyzers)

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
            ui.label("Running Analysis").classes("text-xl font-bold")

            progress_bar = ui.linear_progress(value=0).classes("w-full")

            step_checkboxes = []
            with ui.column().classes("w-full gap-1"):
                primary_checkbox = ui.checkbox(analyzer.name, value=False).props(
                    "disable"
                )
                step_checkboxes.append(primary_checkbox)

                for secondary in secondary_analyzers:
                    checkbox = ui.checkbox(secondary.name, value=False).props("disable")
                    step_checkboxes.append(checkbox)

            log_container = ui.column().classes("w-full gap-1")

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
        current_step = 0

        def poll_queue():
            nonlocal analysis_complete, current_step

            try:
                msg_dict = queue.get_nowait()
            except Empty:
                return

            msg = AnalysisQueueMessage(**msg_dict)

            if msg.type == "analyzer_start":
                current_step += 1
                progress_bar.value = current_step / total_steps
                with log_container:
                    ui.label(f"Starting {msg.analyzer_name}...").classes(
                        "text-sm text-grey-7"
                    )

            elif msg.type == "analyzer_finish":
                if 0 < current_step <= len(step_checkboxes):
                    step_checkboxes[current_step - 1].value = True
                with log_container:
                    ui.label(f"Finished {msg.analyzer_name}").classes(
                        "text-sm text-positive"
                    )

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
        timer = ui.timer(QUEUE_POLL_INTERVAL, poll_queue)

        await run_analysis_task()

        while not analysis_complete:
            await sleep(QUEUE_POLL_INTERVAL)

        timer.cancel()
