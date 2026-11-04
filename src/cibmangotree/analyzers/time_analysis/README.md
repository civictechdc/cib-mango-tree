# Time Analysis

Port of [cib-time-analysis](https://github.com/mattburnett-repo/cib-time-analysis)
into the in-repo analyzer recipe (issue #435).

## Fold

| Piece | Location |
| --- | --- |
| Primary | `time_analysis_base/` — methods → `posts` + `edges` parquet |
| Secondary | none (v1) |
| Dashboard | `gui/dashboards/time_analysis/` — Explore + Compare |
| Manual CSVs | `assets/test_data/time_analysis/` (incl. Truth reduced) |

**Left out:** dataset picker buttons, standalone NiceGUI app shell.

**Params:** `method` (choice: Sliding Window / ADO / Time Overlap; default **Time Overlap**), `win_size` (2), `t_step` (**300**), `min_posts` (20). Smaller `t_step` or Sliding Window can be much slower on long timelines.

`is_distributed=False` until the path is validated end-to-end.
