# Test / QA datasets

Manual and exploratory fixtures. **Not** used by CI analyzer goldens
(`src/cibmangotree/analyzers/*/test_data/`).

## `time_analysis/`

Ported from [cib-time-analysis](https://github.com/mattburnett-repo/cib-time-analysis)
`csv_data/` (Truth uses the **reduced** export).

| File | time | user | content |
| --- | --- | --- | --- |
| `bsky_vax_2024.csv` | `createdAt` | `authorProfile.handle` | `text` |
| `truth_vax_2024-2025_reduced.csv` | `created_at` | `account.username` | `content_cleaned` |
| `russia_troll_tweets.csv` | `Date tweet sent` | `Twitter screenname` | `Tweet text` |

Load via the normal upload → column map path. There is no in-app dataset picker.

Tracked with Git LFS (`assets/test_data/time_analysis/*.csv`).
