# AGENTS.md — CIB Mango Tree

Shared instructions for AI coding agents (Cursor, Claude Code, Codex, etc.).

## What this repo is

**CIB Mango Tree** (Mango Tango CLI) is a Python tool for social media data analysis: import → preprocess → primary/secondary analyzers → web presentation / export. Modular analyzers; Parquet-centric storage.

## Where to load context

1. `.ai-context/README.md` — overview  
2. `.ai-context/architecture-overview.md` — architecture  
3. `.ai-context/symbol-reference.md` — symbol map  
4. `.ai-context/setup-guide.md` — setup  
5. `docs/dev-guide.md` — development guide  

Cursor-specific rules live in `.cursor/rules/`. Claude-oriented notes: `CLAUDE.md`.

## Commands

```bash
uv sync --locked
python -m cibmangotree          # app
python -m cibmangotree --noop   # smoke
isort . && black .              # format
pytest                          # tests
uv run pyinstaller pyinstaller.spec   # GUI bundle
```

## Conventions

- Branch from `main`; PR to upstream `main` (`feature/*`, `bugfix/*`)
- Black + isort; modern type hints; Pydantic validation
- Prefer Polars; co-located pytest + `test_data/`
- No hardcoded secrets; PolyForm Noncommercial 1.0.0

## Packaging note

Windows GitHub Releases currently ship a **zip** of the PyInstaller onedir plus an **MSIX** from the same Windows job (`packaging/msix/` + MakeAppx). Keep the zip. Tagged stable releases also run `publish_msix` in `release.yml`. See `.cursor/skills/windows-store-msix/SKILL.md`.

## MCP (optional)

Cursor MCP: `.cursor/mcp.json`. Servers: Context7 (lib docs), Microsoft Learn (Store/MSIX), NiceGUI docs via `mcpdoc` → `docs/nicegui.io/llm.txt`.
