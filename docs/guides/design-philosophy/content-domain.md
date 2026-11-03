## Content Domain

The Content domain is where the analysis and visualization happen.

An analysis is added to the application by defining a **Primary Analyzer**, which comes with an interface declaration and an implementation. The interface declaration defines the input data structure and the output tables, which the application depends on for user guidance. The implementation is made workspace-agnostic by means of the "context" object.

The goal of the Primary Analyzer is to produce a set of output tables that can be used by other analyzers, including **Secondary Analyzers**. Primary Analyzer outputs are ideally normalized, non-duplicated, and non-redundant. As such, they are not always suitable for direct user consumption. Secondary Analyzers produce user-friendly or export-oriented tables from those primary outputs. Interactive visualization is handled by **NiceGUI dashboards** registered in the GUI (not by a separate presenter layer in the analyzer suite).

Secondary Analyzers are defined with their own interface objects and declare a `base_analyzer` primary. Dashboards read primary and/or secondary parquet outputs and are keyed by primary analyzer id.

## Next Steps

- [Core Domain](./core-domain.md)
- [Edge Domain](./edge-domain.md)
- [Implementing Analyzers](../contributing/analyzers.md)
