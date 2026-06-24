# CLI to GUI transition: contribution roadmap

This directory holds working notes for the move from the command-line tool to the
desktop GUI. It keeps the planning in one place so each piece can be cherry-picked
into a feature branch when the work starts. Every area file is self-contained: it
records what already shipped, what remains, and the specific changes to make.

Check each claim against the current `main` before you start. The branch moved
quickly between late May and early June 2026 (several PRs, including #340, #346,
and #350). Some items below were resolved by those merges and are marked as done
so they are not repeated. A description that a later commit has overtaken should
not be trusted on its own.

## Current architecture

The GUI is built on NiceGUI in a native pywebview window, packaged as a
PyInstaller one-directory bundle. The notes in `.ai-context/architecture-overview.md`
still describe a Dash and Shiny stack; that stack is no longer in `src/`. The
current picture:

- Entry point: `src/cibmangotree/__main__.py`, which calls `gui_main`
  (`src/cibmangotree/gui/main_workflow.py`).
- UI: NiceGUI pages under `src/cibmangotree/gui/`, one page class per screen.
- Analysis: dispatched to a spawned child process through
  `nicegui.run.cpu_bound`, which runs `AnalysisContext.run_worker`.
- Data: Polars over Parquet, rendered with ECharts inside the dashboards.
- Packaging: `pyinstaller.spec`, released through
  `.github/workflows/release.yml` (one workflow since #350), which calls
  `build_gui.yml` for Windows and macOS (x86 and arm64).

The repository description ("interactive python terminal UI wrapper") and the
architecture notes should be updated to match. That edit is worth making and is
not tracked here.

## Where to spend effort

Three areas, ordered by how much they reduce the risk of shipping a broken
release and restore the core workflow. They have few code dependencies on each
other and can run in parallel.

1. Worker process boundary and its tests (`worker-process-boundary.md`). The
   transition moved analysis into a spawned process. That seam produced the one
   break that reached a release (#338) and is where the next one is most likely.
   Half the coverage is already in place; finishing it is cheap and makes the
   other fixes verifiable.
2. Column type mapping and timestamp detection (`column-type-mapping.md`). Time
   columns the CLI handled now dead-end at an empty mapping dropdown (#330 and
   related). The fixes are small and the bug blocks the main workflow on common
   datasets.
3. Windows launch remainder (`windows-launch.md`). The Mark-of-the-Web fix and
   the release-pipeline cleanup already merged. What is left is gating browser
   mode for Windows and two one-line corrections.

`backlog-triage.md` lists issues to close or re-file because they target the
removed Dash, Shiny, and WebGL frontend.

## Conventions for these PRs

- One purpose per PR, with a plain-language description. The maintainers have
  asked for short, curated text rather than long generated write-ups.
- Reference the issue the change closes and state how you verified it.
- Add a test with any change to the worker path or the type mapping.
