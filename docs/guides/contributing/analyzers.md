# Analyzers

Analyzers are the core data-processing components of CIB Mango Tree. Users pick a **primary** analyzer, map columns, set parameters, and run an analysis. The app then runs any **secondary** analyzers bound to that primary: primaries usually write normalized tables meant for further processing, while secondaries turn those into export-friendly or dashboard-ready outputs—so the suite runs them automatically whenever that primary finishes (the user does not pick secondaries separately). Afterward, users can open a **NiceGUI results dashboard** for that primary (a registered dashboard if one exists; otherwise a placeholder).

## Recipe overview

| Piece | Role |
| --- | --- |
| Primary analyzer | Reads user input (parquet), writes declared output tables |
| Secondary analyzer (optional) | Reads primary outputs, writes exportable or derived tables |
| Suite registration | Lists declarations in `analyzers/__init__.py` |
| NiceGUI dashboard (optional) | Results UI keyed by primary analyzer id |

**Templates**

- **Teaching sample:** `src/cibmangotree/analyzers/example/` (`__example__` + `example_report`)
- **Production shape to copy:** `src/cibmangotree/analyzers/ngrams/` (primary + secondary + denormalize + dashboard)

**Registered secondaries are the normal pattern** (see `example_report` and `ngram_stats`). What to avoid is the hashtags **exception**: it has no suite secondary. Instead, `hashtags_base/analysis.py` exposes a helper the dashboard calls live at click-time. That is not a `SecondaryAnalyzerDeclaration`, does not persist secondary outputs, and **must not be copied** when adding a new analyzer. Hashtags stays an intentional do-not-copy exception; use **example** (teaching) or **ngrams** (production shape) instead.

### Extension checklist

1. Create `analyzers/<family>/<name>_base/` with `interface.py`, `main.py`, and `__init__.py` declaration.
2. Optionally add a secondary package with `SecondaryAnalyzerInterface(base_analyzer=…)` and declaration.
3. Register declaration(s) in `analyzers/__init__.py`.
4. Optionally add `gui/dashboards/<name>/` subclassing `BaseDashboardPage` and register it in `_DASHBOARD_REGISTRY`.
5. Add family-level tests and `test_data/`.
6. Set `is_distributed=True` when the primary is ready to ship. Think of it as a **visibility / ship flag**: `False` = listed only in development runs; `True` = listed in development **and** the packaged app. It is not a user-facing toggle inside a running build. Secondaries are not filtered by this flag.

## Primary analyzers

### Layout

Typical package:

```text
analyzers/<family>/<name>_base/
  __init__.py      # AnalyzerDeclaration
  interface.py     # AnalyzerInterface
  main.py          # entry point
  default_params.py  # optional
```

### Interface

```python
from cibmangotree.analyzer_interface import (
    AnalyzerInput,
    AnalyzerInterface,
    AnalyzerOutput,
    AnalyzerParam,
    InputColumn,
    IntegerParam,
    OutputColumn,
)

interface = AnalyzerInterface(
    id="__example__",  # globally unique; stored with analysis data
    version="0.1.0",
    name="Example Analyzer",
    short_description="Example Analyzer (Character Count)",
    long_description="Counts characters in each message.",
    input=AnalyzerInput(
        columns=[
            InputColumn(
                name="message_id",
                human_readable_name="Unique Message ID",
                data_type="identifier",
                description="The unique identifier of the message",
                name_hints=["post", "message", "tweet", "id"],
            ),
            InputColumn(
                name="message_text",
                human_readable_name="Message Text",
                data_type="text",
                description="The text content of the message",
                name_hints=["message", "text", "content", "body"],
            ),
        ]
    ),
    params=[
        AnalyzerParam(
            id="fudge_factor",
            human_readable_name="Character Count Adjustment",
            description="Adds to the character count for testing purposes",
            type=IntegerParam(min=-1000, max=1000),
            default=0,
            backfill_value=0,  # fills missing/None only; preserves 0 / False
        )
    ],
    outputs=[
        AnalyzerOutput(
            id="character_count",
            name="Character Count Per Message",
            internal=True,  # omitted from the export list
            columns=[
                OutputColumn(name="message_id", data_type="integer"),
                OutputColumn(name="character_count", data_type="integer"),
            ],
        )
    ],
)
```

Supported `data_type` values include `text`, `integer`, `float`, `boolean`, `datetime`, `identifier`, `url`, and `time`. The GUI uses these (plus `name_hints`) for column mapping.

### Parameters the GUI can edit

Today the params UI renders:

- `IntegerParam` → integer controls
- `ChoiceParam` → labeled single-select (`ChoiceOption` value/label pairs; value is a `str`)
- `TimeBinningParam` → time-window control (import from `cibmangotree.analyzer_interface.params`; used by hashtags)

Other param types need both a model in `params.py` and a GUI branch. Prefer static `default=` on `AnalyzerParam` when the default does not depend on the dataset.

### `default_params` (optional)

`AnalyzerDeclaration(..., default_params=fn)` can override static defaults. Returning `None` for a key **unsets** a static default.

!!! warning
    The default-params context supports `context.input()` (mapped project input). It does **not** support `params` or `output`. Prefer static `default=` on `AnalyzerParam` when the value does not depend on the dataset. The example’s `default_params` returns `{}`.

### Implementation (`main`)

```python
import polars as pl
from cibmangotree.analyzer_interface.context import PrimaryAnalyzerContext

def main(context: PrimaryAnalyzerContext):
    input_reader = context.input()
    # Required: rename/map columns and apply semantics.
    df_input = input_reader.preprocess(pl.read_parquet(input_reader.parquet_path))

    # Prefer declared interface defaults over hard-coded fallbacks in main.
    fudge_factor = context.params["fudge_factor"]
    assert isinstance(fudge_factor, int)

    with context.progress("Counting characters") as reporter:
        df_count = df_input.select(
            pl.col("message_id"),
            pl.col("message_text")
            .str.len_chars()
            .add(fudge_factor)
            .alias("character_count"),
        )
        reporter.update(1.0)

    df_count.write_parquet(context.output("character_count").parquet_path)
```

Notes:

- Write one parquet per declared output id (`context.output(id).parquet_path`).
- `context.temp_dir` is available for scratch / spill files (ngrams uses this).
- Analysis runs in a **worker subprocess**. Keep imports and entry points picklable and side-effect light at import time.
- Use `with context.progress("step") as reporter:` for optional progress UI (no-op when unset).

### Declaration

```python
from cibmangotree.analyzer_interface import AnalyzerDeclaration
from .default_params import default_params
from .interface import interface
from .main import main

example_base = AnalyzerDeclaration(
    interface=interface,
    main=main,
    default_params=default_params,
    # Visibility / ship flag for this primary:
    # False = development only; True = also shown in the packaged executable.
    is_distributed=False,
)
```

## Secondary analyzers

Secondaries have no user input mapping and no params UI. They bind to a primary via `base_analyzer` and run automatically after that primary (registration order for that primary).

### Interface

```python
from cibmangotree.analyzer_interface import (
    AnalyzerOutput,
    OutputColumn,
    SecondaryAnalyzerInterface,
)
from ..example_base.interface import interface as example_base

interface = SecondaryAnalyzerInterface(
    id="example_report",
    version="0.1.0",
    name="Example Report",
    short_description="Adds an is_long flag to character counts",
    base_analyzer=example_base,
    outputs=[
        AnalyzerOutput(
            id="example_report",
            name="Example Report",
            columns=[
                OutputColumn(name="message_id", data_type="integer"),
                OutputColumn(name="character_count", data_type="integer"),
                OutputColumn(name="is_long", data_type="boolean"),
            ],
        )
    ],
)
```

### Implementation

```python
import polars as pl
from cibmangotree.analyzer_interface.context import SecondaryAnalyzerContext

def main(context: SecondaryAnalyzerContext):
    df = pl.read_parquet(context.base.table("character_count").parquet_path)
    df_export = df.with_columns(pl.col("character_count").gt(100).alias("is_long"))
    # Primary params are available if needed:
    _ = context.base_params.get("fudge_factor")
    df_export.write_parquet(context.output("example_report").parquet_path)
```

### Declaration

```python
from cibmangotree.analyzer_interface import SecondaryAnalyzerDeclaration
from .interface import interface
from .main import main

example_report = SecondaryAnalyzerDeclaration(interface=interface, main=main)
```

### Export denormalization (optional)

`AnalyzerOutput` may set `denormalize=OutputDeNormalization(...)` so exports re-join columns from another output (see `ngrams` / `ngram_stats` / `ngram_full`). Use this when the export should include human-readable columns that stay normalized in the primary tables.

## NiceGUI dashboards

Results visualization is **not** part of `AnalyzerSuite`. Dashboards live under `src/cibmangotree/gui/dashboards/` and subclass `BaseDashboardPage`.

Register by **primary analyzer id** in `gui/dashboards/__init__.py`:

```python
_DASHBOARD_REGISTRY: dict[str, type[BaseDashboardPage]] = {
    "hashtags": HashtagsDashboardPage,
    "ngrams": NgramsDashboardPage,
}
```

If no dashboard is registered, the app shows a placeholder. See existing `ngrams` and `hashtags` dashboard packages for layout patterns. Set `_secondary_analyzer_id` on the page when reading secondary outputs via the base helpers.

## Registering in the suite

```python
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
```

There is no plugin auto-discovery: if it is not in this list, it does not run.

## Testing

Helpers live in `cibmangotree.testing`. Tests usually sit at family level next to a shared `test_data/` directory (see `analyzers/example/`).

### Primary

```python
import os
from cibmangotree.preprocessing.series_semantic import identifier
from cibmangotree.testing import CsvTestData, test_primary_analyzer
from .example_base.interface import interface
from .example_base.main import main
from .test_data import test_data_dir

def test_example_base():
    test_primary_analyzer(
        interface,
        main,
        input=CsvTestData(
            os.path.join(test_data_dir, "input.csv"),
            semantics={"message_id": identifier},
        ),
        params={"fudge_factor": 10},
        outputs={
            "character_count": CsvTestData(
                os.path.join(test_data_dir, "output.csv")
            )
        },
    )
```

### Secondary

```python
from cibmangotree.testing import ParquetTestData, test_secondary_analyzer

def test_example_report():
    test_secondary_analyzer(
        interface,
        main,
        primary_params={"fudge_factor": 10},
        primary_outputs={
            "character_count": ParquetTestData(...),
        },
        expected_outputs={
            "example_report": ParquetTestData(...),
        },
    )
```

`CsvTestData`, `JsonTestData`, and `ParquetTestData` are supported. Comparisons check shape, column set, and dtypes; **row order matters**.

## Best practices

- Always `preprocess()` primary input after reading parquet.
- Declare every output column you write; mark internal outputs with `internal=True` when they should not appear in exports.
- Prefer interface `default=` over duplicating fallbacks inside `main`.
- Use `name_hints` to improve column automap.
- Keep long work in progress steps when useful; use `temp_dir` for large intermediates.

## Next steps

- Study `analyzers/example/` then `analyzers/ngrams/`.
- Design philosophy (domains): [architecture](../design-philosophy/architecture.md), [content](../design-philosophy/content-domain.md), [core](../design-philosophy/core-domain.md), [edge](../design-philosophy/edge-domain.md)
- GUI dashboard code: `src/cibmangotree/gui/dashboards/` and `src/cibmangotree/gui/README.md`.
