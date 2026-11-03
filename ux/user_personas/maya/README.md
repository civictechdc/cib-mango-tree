# Maya

User persona and journey materials for **Maya** — her first time finding copy-pasta with Mango Tree as her guide.

This folder holds UX work product for Maya’s path through the product. Files here are design reference for engineering and product discussion, not runtime assets.

> **Source note:** The journey map describes *how it should work*, not how the product works today. It is built on Mango Tree v0.12.0 screenshots, the CIB Mango Tree literature review (persona **UXP09**, paper **P11**), and research on where to get posts and how Mango Tree spots copy-pasta. Times, numbers, names, and quotes are illustrative. This is a **proto-persona** from the literature review — not yet validated with interviews.

## Persona

| | |
| --- | --- |
| **Name** | Maya |
| **Role** | Reporter |
| **Skills** | Comfortable with spreadsheets. Doesn’t code. Has never downloaded posts from a social site. |
| **What she already knows** | Mango Tree is a free tool people use to check whether posts were copied. She has never used it. |
| **Goals** | Proof she can show her editor. Step-by-step guidance — “Don’t make me learn anything technical.” |
| **Scenario** | At 1:00 pm her editor forwards dozens of posts on X about a school-board vote that all say nearly the same thing: *“Is this coordinated? I need to know by 5.”* |

## Journey map

| File | Description |
| --- | --- |
| [Journey with Mango Tree as her guide.pdf](./user_journey/Journey%20with%20Mango%20Tree%20as%20her%20guide.pdf) | Full journey board: persona, steps 1–16, thoughts/feelings, screen ideas, guidance principles, stuck points, and key moments |

### Phases (illustrative timeline)

1. **Getting started** — 1:00 to 1:10 pm  
2. **Getting the posts** — 1:10 to 1:45 pm  
3. **Making sure they’re the right posts** — 1:45 to 2:00 pm  
4. **Understanding what was found** — 2:00 to 2:40 pm  
5. **Taking it to her editor** — 2:40 to 3:00 pm  

### Steps (product path)

| # | What she does | Screen |
| --- | --- | --- |
| 1 | Notices something | Social feed (outside Mango Tree) |
| 2 | Opens Mango Tree | Home page |
| 3 | Gets a quick welcome | Welcome |
| 4 | Picks the Copy-Pasta Finder | Tools |
| 5 | Chooses where the posts are | Pick a site |
| 6 | Chooses how to get them | Ways to get posts |
| 7 | Gets the posts from the site | Step-by-step guide |
| 8 | Adds her posts | Add your posts |
| 9 | Pastes a post she noticed | What did you notice? |
| 10 | Confirms these are the right posts | Is this it? |
| 11 | Mango Tree looks for copies | Progress |
| 12 | Sees the main finding | Findings |
| 13 | Looks inside a group | Group detail |
| 14 | Reads what it can’t prove | Group detail |
| 15 | Downloads a summary | Summary |
| 16 | Decides what to do next | Her story |

**Bluesky shortcut:** Mango Tree can get the posts itself — she skips to step 9. Solid path = X / Instagram / TikTok / Telegram (step-by-step guide); dashed path = Bluesky (no effort).

### Key moments (from the board)

- **Moment that matters most — steps 7 to 10:** Getting the right posts. She leaves Mango Tree, may not come back, and could return with the wrong posts. It ends when she says “Yes, that’s it.”
- **The main picture — steps 12 and 13:** A timeline where each dot is one post; copied posts bunch together. She learns to read it once.

## Folder contents

```text
maya/
  README.md                                      # this file
  user_journey/
    Journey with Mango Tree as her guide.pdf     # journey map
    screens/                                     # optional — screen exports by step
    handoff/                                     # optional — packs marked ready for eng
  agent/
    requirements.md                              # PoC pass/fail checklist for code review
```

Suggested naming for new exports under `user_journey/`: `<step_or_screen>_<descriptor>.png` (for example `welcome_overview.png`, `add_your_posts.png`).

### Maya agent (prototype)

- Checklist for code/diff review: [agent/requirements.md](./agent/requirements.md)
- Cursor skills live under **`.cursor/skills/user_personas/`** (gitignored locally):

| Path | Purpose |
| --- | --- |
| `maya/` | Roleplay as Maya (`maya` skill) |
| `maya-review/` | Audit code/diffs against `agent/requirements.md` (`maya-review` skill) |

## Using these assets

1. Read this README and the journey PDF before implementing Maya-facing flows.
2. Match screens to product steps; note gaps or open questions in PRs or issues.
3. When an export is approved for the product or docs, copy it to the right destination (`docs/img/`, packaging, or GUI assets) — do not load files from `ux/` at runtime.
4. See [ux/README.md](../../README.md) for repo-wide UX conventions.

## Open questions / TODOs for UX

- Validate the proto-persona with interviews.
- Add Figma or prototype links here when available.
- Call out which journey steps are **ready for engineering** vs. still exploratory.
