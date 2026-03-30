import os
from functools import cached_property
from multiprocessing import Event, Queue
from tempfile import TemporaryDirectory
from typing import Callable, Literal

from pydantic import BaseModel, ConfigDict

from analyzer_interface import (
    AnalyzerDeclaration,
    SecondaryAnalyzerDeclaration,
    backfill_param_values,
)
from analyzer_interface.context import ProgressReporterProtocol
from context import (
    InputColumnProvider,
    PrimaryAnalyzerContext,
    SecondaryAnalyzerContext,
)
from storage import AnalysisModel

from .app_context import AppContext
from .project_context import ProjectContext


class AnalysisQueueMessage(BaseModel):
    type: Literal[
        "analyzer_start",
        "analyzer_finish",
        "step_start",
        "step_progress",
        "step_finish",
        "log",
        "error",
        "complete",
        "cancelled",
    ]
    analyzer_id: str | None = None
    analyzer_name: str | None = None
    step_name: str | None = None
    step_progress: float | None = None
    message: str | None = None
    progress: float | None = None


class AnalysisRunProgressEvent(BaseModel):
    analyzer: AnalyzerDeclaration | SecondaryAnalyzerDeclaration
    event: Literal["start", "finish"]


class AnalysisContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    app_context: AppContext
    project_context: ProjectContext
    model: AnalysisModel
    is_deleted: bool = False

    @property
    def display_name(self):
        return self.model.display_name

    @property
    def id(self):
        return self.model.analysis_id

    @property
    def analyzer_id(self):
        return self.model.primary_analyzer_id

    @property
    def analyzer_spec(self):
        analyzer = self.app_context.suite.get_primary_analyzer(self.analyzer_id)
        assert analyzer, f"Analyzer `{self.analyzer_id}` not found"
        return analyzer

    @property
    def column_mapping(self):
        return self.model.column_mapping

    @property
    def create_time(self):
        return self.model.create_time()

    @cached_property
    def backfilled_param_values(self):
        return backfill_param_values(self.model.param_values, self.analyzer_spec)

    @property
    def is_draft(self):
        return self.model.is_draft

    @cached_property
    def web_presenters(self):
        return self.app_context.suite.find_web_presenters(self.analyzer_spec)

    def web_server(self):
        from .analysis_webserver_context import AnalysisWebServerContext

        return AnalysisWebServerContext(
            app_context=self.app_context, analysis_context=self
        )

    def rename(self, new_name: str):
        self.model.display_name = new_name
        self.app_context.storage.save_analysis(self.model)

    def delete(self):
        self.is_deleted = True
        self.app_context.storage.delete_analysis(self.model)

    def run(self):
        from terminal_tools import ProgressReporter

        assert not self.is_deleted, "Analysis is deleted"
        secondary_analyzers = (
            self.app_context.suite.find_toposorted_secondary_analyzers(
                self.analyzer_spec
            )
        )

        progress_reporter_factory: Callable[[str], ProgressReporterProtocol] = (
            lambda step_name: ProgressReporter(step_name)
        )

        with TemporaryDirectory() as temp_dir:
            yield AnalysisRunProgressEvent(analyzer=self.analyzer_spec, event="start")
            analyzer_context = PrimaryAnalyzerContext(
                analysis=self.model,
                analyzer=self.analyzer_spec,
                store=self.app_context.storage,
                temp_dir=temp_dir,
                input_columns={
                    analyzer_column_name: InputColumnProvider(
                        user_column_name=user_column_name,
                        semantic=self.project_context.column_dict[
                            user_column_name
                        ].semantic,
                    )
                    for analyzer_column_name, user_column_name in self.column_mapping.items()
                },
                progress_reporter=progress_reporter_factory,
            )
            analyzer_context.prepare()
            self.analyzer_spec.entry_point(analyzer_context)
            yield AnalysisRunProgressEvent(analyzer=self.analyzer_spec, event="finish")

        for secondary in secondary_analyzers:
            yield AnalysisRunProgressEvent(analyzer=secondary, event="start")
            with TemporaryDirectory() as temp_dir:
                analyzer_context = SecondaryAnalyzerContext(
                    analysis=self.model,
                    secondary_analyzer=secondary,
                    temp_dir=temp_dir,
                    store=self.app_context.storage,
                    progress_reporter=progress_reporter_factory,
                )
                analyzer_context.prepare()
                secondary.entry_point(analyzer_context)
            yield AnalysisRunProgressEvent(analyzer=secondary, event="finish")

        self.model.is_draft = False
        self.app_context.storage.save_analysis(self.model)

    @staticmethod
    def run_worker(
        analysis_model: AnalysisModel,
        analyzer_id: str,
        column_mapping: dict[str, str],
        input_columns_data: dict[str, tuple[str, str]],
        secondary_analyzer_ids: list[str],
        storage,
        queue: Queue,
        cancel_event: Event,
    ) -> AnalysisModel:
        """
        Static method to run analysis in a separate process.

        This method is designed to be called via ui.run.cpu_bound().

        See: https://github.com/zauberzeug/nicegui/discussions/1046#discussioncomment-6225227

        Args:
            analysis_model: The analysis model
            analyzer_id: The primary analyzer ID
            column_mapping: Mapping from analyzer column names to user column names
            input_columns_data: Dict of analyzer_column_name -> (user_column_name, semantic_name)
            secondary_analyzer_ids: List of secondary analyzer IDs
            storage: Storage instance
            queue: Multiprocessing queue for progress messages
            cancel_event: Multiprocessing event to signal cancellation

        Returns:
            The updated analysis model (is_draft=False on success)
        """
        from analyzers import suite
        from preprocessing.series_semantic import all_semantics

        from .gui_progress_reporter import GUIProgressReporter

        analyzer_spec = suite.get_primary_analyzer(analyzer_id)
        if analyzer_spec is None:
            queue.put(
                AnalysisQueueMessage(
                    type="error",
                    message=f"Analyzer '{analyzer_id}' not found",
                ).model_dump()
            )
            return analysis_model

        secondary_analyzers = [
            sec
            for sec_id in secondary_analyzer_ids
            if (sec := suite.get_secondary_analyzer_by_id(analyzer_id, sec_id))
            is not None
        ]

        semantic_lookup = {s.semantic_name: s for s in all_semantics}

        def send_message(msg: AnalysisQueueMessage):
            queue.put(msg.model_dump())

        def check_cancelled() -> bool:
            return cancel_event.is_set()

        def make_progress_reporter(
            analyzer_id: str, analyzer_name: str
        ) -> Callable[[str], ProgressReporterProtocol]:
            def factory(step_name: str) -> ProgressReporterProtocol:
                return GUIProgressReporter(
                    queue=queue,
                    analyzer_id=analyzer_id,
                    analyzer_name=analyzer_name,
                    step_name=step_name,
                )

            return factory

        try:
            with TemporaryDirectory() as temp_dir:
                if check_cancelled():
                    send_message(AnalysisQueueMessage(type="cancelled"))
                    return analysis_model

                send_message(
                    AnalysisQueueMessage(
                        type="analyzer_start",
                        analyzer_id=analyzer_spec.id,
                        analyzer_name=analyzer_spec.name,
                    )
                )

                input_columns = {
                    analyzer_col_name: InputColumnProvider(
                        user_column_name=user_col_name,
                        semantic=semantic_lookup[semantic_name],
                    )
                    for analyzer_col_name, (
                        user_col_name,
                        semantic_name,
                    ) in input_columns_data.items()
                }

                analyzer_context = PrimaryAnalyzerContext(
                    analysis=analysis_model,
                    analyzer=analyzer_spec,
                    store=storage,
                    temp_dir=temp_dir,
                    input_columns=input_columns,
                    progress_reporter=make_progress_reporter(
                        analyzer_spec.id, analyzer_spec.name
                    ),
                )
                analyzer_context.prepare()

                if check_cancelled():
                    send_message(AnalysisQueueMessage(type="cancelled"))
                    return analysis_model

                analyzer_spec.entry_point(analyzer_context)

                if check_cancelled():
                    send_message(AnalysisQueueMessage(type="cancelled"))
                    return analysis_model

                send_message(
                    AnalysisQueueMessage(
                        type="analyzer_finish",
                        analyzer_id=analyzer_spec.id,
                        analyzer_name=analyzer_spec.name,
                    )
                )

            for secondary_spec in secondary_analyzers:
                if check_cancelled():
                    send_message(AnalysisQueueMessage(type="cancelled"))
                    return analysis_model

                send_message(
                    AnalysisQueueMessage(
                        type="analyzer_start",
                        analyzer_id=secondary_spec.id,
                        analyzer_name=secondary_spec.name,
                    )
                )

                with TemporaryDirectory() as temp_dir:
                    secondary_context = SecondaryAnalyzerContext(
                        analysis=analysis_model,
                        secondary_analyzer=secondary_spec,
                        temp_dir=temp_dir,
                        store=storage,
                        progress_reporter=make_progress_reporter(
                            secondary_spec.id, secondary_spec.name
                        ),
                    )
                    secondary_context.prepare()

                    if check_cancelled():
                        send_message(AnalysisQueueMessage(type="cancelled"))
                        return analysis_model

                    secondary_spec.entry_point(secondary_context)

                send_message(
                    AnalysisQueueMessage(
                        type="analyzer_finish",
                        analyzer_id=secondary_spec.id,
                        analyzer_name=secondary_spec.name,
                    )
                )

            analysis_model.is_draft = False
            storage.save_analysis(analysis_model)
            send_message(AnalysisQueueMessage(type="complete"))
            return analysis_model

        except Exception as e:
            send_message(
                AnalysisQueueMessage(
                    type="error",
                    message=str(e),
                )
            )
            raise

    @property
    def export_root_path(self):
        return self.app_context.storage._get_project_exports_root_path(self.model)

    def export_directory_exists(self) -> bool:
        return os.path.exists(self.export_root_path)

    def get_all_exportable_outputs(self):
        from .analysis_output_context import AnalysisOutputContext

        return [
            *(
                AnalysisOutputContext(
                    app_context=self.app_context,
                    analysis_context=self,
                    secondary_spec=None,
                    output_spec=output,
                )
                for output in self.analyzer_spec.outputs
                if not output.internal
            ),
            *(
                AnalysisOutputContext(
                    app_context=self.app_context,
                    analysis_context=self,
                    secondary_spec=secondary,
                    output_spec=output,
                )
                for secondary_id in self.app_context.storage.list_secondary_analyses(
                    self.model
                )
                if (
                    secondary := self.app_context.suite.get_secondary_analyzer_by_id(
                        self.analyzer_id, secondary_id
                    )
                )
                is not None
                for output in secondary.outputs
                if not output.internal
            ),
        ]
