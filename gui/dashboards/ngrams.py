"""
N-grams results dashboard page.

Displays an interactive scatter plot of n-gram frequency vs. unique poster
count, loaded from the ``ngram_stats`` secondary analyzer output.
"""

import polars as pl
from nicegui import ui

from analyzers.ngrams.ngrams_stats.interface import OUTPUT_NGRAM_STATS
from analyzers.ngrams.ngrams_stats.interface import interface as ngram_stats_interface
from analyzers.ngrams.ngrams_web.plots import plot_scatter
from gui.base import GuiSession

from .base_dashboard import BaseDashboardPage


class NgramsDashboardPage(BaseDashboardPage):
    """
    Results dashboard for the N-grams (Copy-Pasta Detector) analyzer.

    Renders a log-log scatter plot of n-gram frequency versus unique poster
    count.  Each point represents one n-gram; points are coloured by n-gram
    length.
    """

    def __init__(self, session: GuiSession):
        super().__init__(session=session)

    def _load_stats(self) -> pl.DataFrame | None:
        """
        Load the ngram_stats output parquet for the current analysis.

        Returns None (and shows an error notification) if the analysis or
        its output files are missing.
        """
        analysis = self.session.current_analysis
        if analysis is None:
            self.notify_error("No analysis found in the current session.")
            return None

        storage = self.session.app.context.storage
        try:
            parquet_path = storage.get_secondary_output_parquet_path(
                analysis,
                ngram_stats_interface.id,
                OUTPUT_NGRAM_STATS,
            )
            df = pl.read_parquet(parquet_path)
        except Exception as exc:
            self.notify_error(f"Could not load n-gram results: {exc}")
            return None

        # Cast n-gram length to string so Plotly treats it as a discrete colour category
        df = df.with_columns(pl.col("n").cast(pl.String))
        return df

    def render_content(self) -> None:
        """Render the scatter plot in a full-width card."""
        df = self._load_stats()

        with ui.column().classes("w-full q-pa-md gap-4"):
            if df is None or df.is_empty():
                with ui.card().classes("w-full items-center q-pa-xl"):
                    ui.icon("bar_chart", size="3rem").classes("text-grey-5")
                    ui.label("No n-gram data available.").classes(
                        "text-subtitle1 text-grey-6 q-mt-sm"
                    )
                return

            fig = plot_scatter(df)

            with ui.card().classes("w-full"):
                with ui.card_section():
                    ui.label("N-gram statistics").classes("text-h6")
                ui.plotly(fig).classes("w-full").style("height: 500px")
