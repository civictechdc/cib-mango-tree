from cibmangotree.analyzer_interface import ParamValue
from cibmangotree.analyzer_interface.context import PrimaryAnalyzerContext


def default_params(context: PrimaryAnalyzerContext) -> dict[str, ParamValue]:
    # Optional override of static interface defaults. Data-dependent defaults
    # override static defaults; returning ``None`` for a key unsets a static
    # default.
    #
    # The default-params context supports ``context.input()`` (project input
    # parquet + column mapping). It does **not** support ``params`` or
    # ``output``. Prefer static ``default=`` on ``AnalyzerParam`` when the
    # value does not depend on the dataset.
    return {}
