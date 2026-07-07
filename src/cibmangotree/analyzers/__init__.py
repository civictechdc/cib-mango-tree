from cibmangotree.analyzer_interface import AnalyzerSuite

from .example.example_base import example_base
from .example.example_report import example_report
from .hashtags.hashtags_base import hashtags
from .ngrams.ngrams_base import ngrams
from .ngrams.ngrams_stats import ngrams_stats

suite = AnalyzerSuite(
    all_analyzers=[
        example_base,
        example_report,
        ngrams,
        ngrams_stats,
        hashtags,
    ]
)
