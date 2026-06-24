# Backlog triage

These issues predate the NiceGUI rewrite and point at code that is no longer in
`src/`. Close or re-file them so the open list reflects the current app.

## Close as superseded

- #184 (convert to pure Shiny, remove the five-layer stack). The Dash, Shiny,
  Flask, and a2wsgi layers it describes are gone from `src/`; only transitive
  dependencies of NiceGUI remain, and the dashboards are NiceGUI. There is
  nothing left to collapse. Close with a pointer to
  `src/cibmangotree/gui/dashboards/`.
- #137 (Gini line chart). Implemented as `plot_gini_echart` in
  `src/cibmangotree/gui/dashboards/hashtags/plots.py`.

## Re-file against the current dashboards

- #152, #153, #154, #155, and #133 describe a WebGL scatter component and an
  `/api/presenters` download endpoint. The current dashboards use ECharts and
  have neither. The underlying requests (axis labels, export, tooltip and zoom
  behavior) are reasonable; re-file them against the ECharts dashboards and close
  the originals.
- #190 and #262 (search and export on the copypasta dashboard) target the Shiny
  version. Re-file against the NiceGUI ngrams dashboard, where
  `filter_ngrams_by_text` already exists.

## In-stack, worth doing later

- #257, #259, #260 (copypasta label, column width, row numbers), #351 (project
  overview table), and #314 (time-window visualization). Small, contributor
  friendly, and against live components. Not on the transition's critical path.
- #187 (time coordination analyzer). The analyzer exists under
  `src/cibmangotree/analyzers/time_coordination/` but is not registered in
  `analyzers/__init__.py` and has no dashboard. Registering it and adding a
  dashboard is the most complete of the new-analyzer requests.

## Defer

- #341, #171, #20 (large-dataset handling). The dashboard already caps display at
  50,000 rows (`src/cibmangotree/gui/dashboards/ngrams/plots.py:70`). The
  remaining limit is the roughly 2 GB per-page memory ceiling of the webview and
  ECharts, which a row cap cannot fully solve. A reasonable small step is to make
  the cap aware of available memory and warn the user; the larger streaming
  rework is not funded now.
- #169 (burst-rate detector). Not in the repository; the thread's work was a
  standalone script, described by its author as not yet specific enough to be
  reliable.
- #289 (multiple GUI sessions). The single-window pywebview model is intentional.
  Relevant only if the project moves to a hosted multi-user mode.
