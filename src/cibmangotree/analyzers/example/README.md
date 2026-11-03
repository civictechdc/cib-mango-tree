# Example Analyzer Implementation

Teaching sample for the analyzer recipe. It counts **characters** (not words) in a text column, then a secondary analyzer adds an `is_long` flag for export.

There is **no** web presenter module. Results UIs are NiceGUI dashboards registered separately (see the [Analyzers](../../../../docs/guides/contributing/analyzers.md) guide and `gui/dashboards/`).

- [Primary Analyzer](./example_base/__init__.py)
- [Secondary Analyzer](./example_report/__init__.py)
- [Test for Primary Analyzer](./test_example_base.py)
- [Test for Secondary Analyzer](./test_example_report.py)
