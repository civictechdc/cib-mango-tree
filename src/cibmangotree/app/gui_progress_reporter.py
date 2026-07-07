from multiprocessing import Queue

from .analysis_context import AnalysisQueueMessage


class GUIProgressReporter:
    """Progress reporter that sends messages to GUI queue."""

    def __init__(
        self,
        queue: Queue,
        analyzer_id: str,
        analyzer_name: str,
        step_name: str,
    ):
        self.queue = queue
        self.analyzer_id = analyzer_id
        self.analyzer_name = analyzer_name
        self.step_name = step_name

    def update(self, value: float):
        self.queue.put(
            AnalysisQueueMessage(
                type="step_progress",
                analyzer_id=self.analyzer_id,
                step_name=self.step_name,
                step_progress=value,
            ).model_dump()
        )

    def finish(self, done_text: str = "Done!"):
        self.queue.put(
            AnalysisQueueMessage(
                type="step_finish",
                analyzer_id=self.analyzer_id,
                analyzer_name=self.analyzer_name,
                step_name=self.step_name,
            ).model_dump()
        )

    def __enter__(self):
        self.queue.put(
            AnalysisQueueMessage(
                type="step_start",
                analyzer_id=self.analyzer_id,
                analyzer_name=self.analyzer_name,
                step_name=self.step_name,
            ).model_dump()
        )
        return self

    def __exit__(self, *args):
        self.finish()
