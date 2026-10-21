from functools import cached_property
from typing import Union

from pydantic import BaseModel

from cibmangotree.analyzer_interface import (
    AnalyzerDeclaration,
    AnalyzerInterface,
    SecondaryAnalyzerDeclaration,
)
from cibmangotree.meta import is_development


class AnalyzerSuite(BaseModel):
    all_analyzers: list[Union[AnalyzerDeclaration, SecondaryAnalyzerDeclaration]]

    @cached_property
    def primary_anlyzers(self):
        return [
            analyzer
            for analyzer in self.all_analyzers
            if isinstance(analyzer, AnalyzerDeclaration)
            if analyzer.is_distributed or is_development()
        ]

    @cached_property
    def _primary_analyzers_lookup(self):
        return {analyzer.id: analyzer for analyzer in self.primary_anlyzers}

    def get_primary_analyzer(self, analyzer_id):
        return self._primary_analyzers_lookup.get(analyzer_id)

    @cached_property
    def _secondary_analyzers(self):
        return [
            analyzer
            for analyzer in self.all_analyzers
            if isinstance(analyzer, SecondaryAnalyzerDeclaration)
        ]

    @cached_property
    def _secondary_analyzers_by_base(self):
        result: dict[str, dict[str, SecondaryAnalyzerDeclaration]] = {}
        for secondary in self._secondary_analyzers:
            base_analyzer = secondary.base_analyzer
            result.setdefault(base_analyzer.id, {}).update({secondary.id: secondary})
        return result

    def find_toposorted_secondary_analyzers(
        self, primary_analyzer: AnalyzerInterface
    ) -> list[SecondaryAnalyzerDeclaration]:
        return list(
            self._secondary_analyzers_by_base.get(primary_analyzer.id, {}).values()
        )

    def get_secondary_analyzer_by_id(self, analyzer_id, secondary_id):
        return self._secondary_analyzers_by_base.get(analyzer_id, {}).get(secondary_id)
