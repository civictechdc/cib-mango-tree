# UX

Design and research work product for CIB Mango Tree.

This folder is the **source of truth for UX handoff** — personas, journeys, flows, screen exports, and related notes from the UX team. It is not loaded by the app at runtime.

If the content weight of this folder gets excessive, we will need to consider spinning off this folder to a separate repo. For now, however, we have collectively decided to start with this in-project folder as a central source of UX-related assets.

## External resources

Links to UX material that lives outside this repo (Google Docs, Figma, Drive folders, Slack canvases, and other remote sources). Prefer a short label plus URL. Persona-specific links can also live in that persona’s README.

_Add entries below as they come in._

[Mika: Figma CIB Desktop App Wireframes](https://www.figma.com/design/as3nSyr2Uu8MZxfKuqNQBk/CIB_DesktopApp?node-id=0-1&p=f&t=wBBf9o4pqvDnF0fY-0)
[Ben S: Google Drive Time Analysis Module Comments](https://docs.google.com/document/d/15OWdyCYKZ84hLtYedJFgTX1-6chpa1vgmrc2EO4Shyk/edit?tab=t.0#heading=h.z3gtdpzc7szw)

## What belongs here

- User personas and journey maps
- Wireframes, mockups, and screen exports ready for engineering
- Research notes, flows, and acceptance context that explain *why* a screen exists
- Brand or component references that guide implementation (when they are part of a UX drop)

## What does not belong here

| Location                | Use instead for                              |
| ----------------------- | -------------------------------------------- |
| `assets/`               | Product/demo data the app or docs consume    |
| `docs/img/`             | Images embedded in project documentation     |
| `packaging/`            | Store / installer icons and packaging assets |
| `src/cibmangotree/gui/` | Implemented UI, theme, and styles            |

When a design asset is **chosen for use** in the product or docs, copy or export it into the appropriate path above. Leave the original under `ux/` so the design history stays intact.

## Layout

```text
ux/
  README.md                      # this file
  user_personas/
    <persona>/                   # one folder per persona (e.g. maya)
      README.md                  # who this persona is + what’s in the folder
      user_journey/              # journey maps, screens, handoff packs
      agent/                     # optional — persona agent checklist / review inputs
```

Add more top-level folders later only when needed (for example shared brand kits that are not tied to one persona). Prefer keeping persona-specific work under `user_personas/<persona>/`.

Cursor skills for persona agents (roleplay / code review) live under `.cursor/skills/user_personas/` and are local/gitignored — they are not part of this tracked `ux/` tree.

## Conventions

1. **Persona folders** use lowercase names (`maya`, not `Maya`).
2. **One persona per folder.** Shared cross-persona material can live at `ux/` or in a clearly named shared subfolder if it appears.
3. **Name files for the step or screen**, not generic dumps (`welcome_screen.png`, not `Export-final-v3.png`).
4. **Include a short README** in each persona folder describing the persona and listing key files.
5. **Link out when useful.** Figma or prototype URLs belong in the persona README; large working files can stay in design tools if the repo holds exports + context.
6. **Handoff means ready for engineering** — exports plus enough notes that a developer can implement without guessing intent.

## For engineers

1. Read the persona README and journey materials first.
2. Treat files under `ux/` as design reference, not runtime assets.
3. Promote finished assets into `docs/img/`, packaging, or GUI static paths when they ship.
4. Match implementation to existing GUI patterns in `src/cibmangotree/gui/` and `docs/guides/contributing/styling.md`.

## For the UX team

Drop new work under the matching `user_personas/<persona>/` folder (or propose a new persona folder). Journey assets go in `user_journey/`; agent/review checklists in `agent/` when present. Prefer clear filenames and a brief note in that persona’s README when you add a major file or revise a journey.
