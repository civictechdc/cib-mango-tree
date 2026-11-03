# Maya requirements (PoC checklist)

Pass/fail checks implied by the Maya persona and journey board (*how it should work*, not necessarily how CIBMT works today).

**Statuses:** `Met` · `Partial` · `Missing` · `N/A` (change set does not touch this surface)

**PoC note:** Keep this list short. Evidence = user-visible copy or flow in code (quote it). Do not invent UI.

| ID | Requirement (Maya language) | Look here first |
| --- | --- | --- |
| R1 | First useful screen leads with my question (find copied / same words), not “create a project” as the main job | `src/cibmangotree/gui/pages/start.py`, `src/cibmangotree/gui/components/new_project_dialog.py` |
| R2 | I get a short, skippable welcome that shows the path ahead in plain English | GUI welcome / onboarding copy under `src/cibmangotree/gui/` |
| R3 | Tools are named for what they find (e.g. “Copy-Pasta Finder”), not “analyzer” jargon | `src/cibmangotree/gui/pages/analyzer_select.py`, analyzer display names |
| R4 | Before I fetch data, I see where posts came from and how much effort each site takes | Import / site-selection UI under `src/cibmangotree/gui/` |
| R5 | One recommended way to get posts; other ways stay folded until I ask | Import / get-posts guidance in GUI |
| R6 | Step-by-step get-posts help I can follow (and return from) without learning technical terms | Import docs/UI copy; `src/cibmangotree/gui/pages/importer.py` |
| R7 | I can drop a file exactly as downloaded — no cleanup / spreadsheet expertise required | `src/cibmangotree/gui/pages/importer.py` and related import components |
| R8 | I can paste one post word-for-word (or pick one) so the tool searches exact words | Analysis / seed-post UI if present; else note Missing |
| R9 | I confirm “yes, that’s it” / “not quite” on the right posts before a long run | Preview / confirm step before run (`dataset_preview`, workflow steps) |
| R10 | While it runs, I see plain progress — not a silent wait or a control panel of choices | `src/cibmangotree/gui/pages/analysis_workflow/run_step.py` |
| R11 | Findings start with one plain sentence before charts; groups ranked simply | Dashboard / findings UI under `src/cibmangotree/gui/dashboards/` |
| R12 | Limits of what this proves sit next to the finding (not buried in help) | Same dashboards / export copy |
| R13 | I can download a short summary I could show my editor | Export / summary actions in GUI (`export_outputs`, dashboards) |

## Out of scope for this PoC

- Interview validation of the persona  
- Automated e2e tests tied to these IDs  
- Full file-by-file code map  

## Source

- [README.md](../README.md) — persona summary  
- [Journey with Mango Tree as her guide.pdf](../user_journey/Journey%20with%20Mango%20Tree%20as%20her%20guide.pdf) — journey board  

