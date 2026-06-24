# Worker process boundary

## Context

The CLI ran analysis in the same process as the interface. The GUI dispatches it
to a child process. `src/cibmangotree/gui/components/stepper_steps/run_step.py`
calls `nicegui.run.cpu_bound(...)`, which starts a process that runs
`AnalysisContext.run_worker` (`src/cibmangotree/app/analysis_context.py`). The
start method is `spawn` on every platform (`src/cibmangotree/__main__.py:17`), so
the child does not inherit the parent's imported modules or `sys.path`.

All analysis data passes through this boundary, and the only break that reached a
release came from it. #338 was a non-namespaced `from analyzers import suite` that
resolved in development, where `src/cibmangotree/` sat on the path, and failed in
the packaged child process. It was fixed in #340; `analysis_context.py:123-126`
now uses absolute `cibmangotree.` imports.

## Already in place

- Cross-platform test matrix: `.github/workflows/test.yml` runs pytest on
  ubuntu-latest, macos-15, and windows-2022.
- Packaged-binary smoke test: `.github/workflows/build_gui.yml` runs the built
  executable with `--noop` on each platform (lines 33, 46, 59, 129-130). The flag
  is handled in `__main__.py:27-42`.

Both are merged. Do not re-propose them.

## Open work

### 1. Tolerance in the snapshot comparer

`src/cibmangotree/testing/comparers.py:31` compares result frames with
`actual.equals(expected)`, an exact match, and line 44 compares cells with `!=`.
Floating-point drift then fails a test whose values are mathematically equal: the
hashtag analyzer's `gini_smooth` reads `0.0` against `4.6e-18` (noted in #339). A
Polars upgrade or a different CPU flips the result.

Replace the exact comparison with
`polars.testing.assert_frame_equal(..., rtol=1e-5, atol=1e-8)` and add
`test_comparers.py` covering an exact match, epsilon noise that must pass, and a
real difference that must fail. `atol=1e-8` sits well below any gini difference
that carries meaning.

### 2. Import-resolution guard

No test imports the modules `run_worker` loads in the child. The draft on this
branch, `src/cibmangotree/app/test_worker_imports.py`, spawns a fresh interpreter,
imports `cibmangotree.analyzers.suite`,
`cibmangotree.preprocessing.series_semantic`, and
`cibmangotree.app.gui_progress_reporter`, and asserts a clean exit. It runs in
about a second and closes the #338 class without starting NiceGUI.

### 3. End-to-end worker dispatch

Add a test that drives `run_worker` through
`multiprocessing.get_context("spawn").Process` against the `example` analyzer's
data and asserts the completion message lands on the queue. Forcing `spawn`
exercises the picklability and start-method behavior that only appears off Linux.

### 4. Crash handling in the progress dialog

`run_step.py` signals completion only when a terminal message arrives on the
queue. A child that dies without enqueuing one, from a segfault, an
out-of-memory kill, or an unpicklable return value, leaves the dialog waiting.
Treat the `cpu_bound` call's return or exception as the source of truth: set the
completion flag in a `finally` and show a terminal state, so a dead child cannot
hang the interface. This matches the "Connection lost" with no recovery reported
in #341.

## Sequence

Items 1 and 2 take about an hour each and can share one PR. Items 3 and 4 are
larger; keep them separate. Land 1 and 2 first so the type-mapping work in
`column-type-mapping.md` can be checked against the worker path.

## References

#338, #339, #340; `analysis_context.py`, `run_step.py`, `testing/comparers.py`.
