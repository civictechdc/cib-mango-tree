# Installation

This guide sets up a **development** environment so you can run and change CIB Mango Tree from source. For a packaged build, use the [latest release](https://github.com/civictechdc/cib-mango-tree/releases/latest) instead.

To try the app **without** a local install, open a [GitHub Codespace](https://codespaces.new/civictechdc/cib-mango-tree) (GitHub account required). The first start can take several minutes while dependencies install; a “starting…” page may appear and refresh until the app is ready in the browser on port 8000. You do not need to run terminal commands. Later opens of the same Codespace are usually much faster.

## Required software

| Software | Needed for |
| --- | --- |
| Python ≥ 3.12 | Runtime and tooling |
| [uv](https://docs.astral.sh/uv/) | Virtual environment and dependencies (recommended) |
| Git | Clone and contribute |
| Terminal | Run install and launch commands |

!!! example
    If you need installers: [Git](https://git-scm.com/install/), [Python](https://www.python.org/downloads/), [uv](https://docs.astral.sh/uv/getting-started/installation/).

## System requirements

- OS: Windows, macOS, or Linux
- Memory: 4GB+ RAM (more helps with large datasets)
- Storage: 1GB+ free (virtual environment, project data)

## Setting up the development environment

### 1. Clone the repository

```bash
git clone https://github.com/civictechdc/cib-mango-tree.git
cd cib-mango-tree
```

### 2. Install dependencies with uv

From the repository root:

```bash
uv sync --group dev
```

This creates `.venv` if needed and installs the project plus the `dev` dependency group from `pyproject.toml`.

??? tip "Working on documentation?"

    Install the docs tools as well (zensical and related packages):

    ```bash
    uv sync --all-groups
    ```

    Preview the site locally with:

    ```bash
    uv run zensical serve --open
    ```

!!! note "Verify Python version"

    ```bash
    uv run python --version   # should be Python 3.12.x
    ```

### 3. Set up pre-commit hooks

Hooks are defined in `.pre-commit-config.yaml`: **Black**, **isort**, and the
local **gui-styles** check (GUI class/style conventions; see
[Styling](../contributing/styling.md)). Install them once:

```bash
uv run pre-commit install
```

Hooks run on `git commit` for matching staged files (not on `git push`).
Formatting hooks may modify files; `gui-styles` only reports violations.

!!! tip "Check everything before pushing"

    ```bash
    uv run pre-commit run --all-files
    ```

### 4. Verify installation

```bash
uv run cibmt --noop
```

You should see:

```text
No-op flag detected. All runtime imports loaded successfully.
```

You can also activate `.venv` and call `cibmt` / `cibmangotree` directly:

=== "macOS / Linux"

    ```bash
    source .venv/bin/activate
    cibmt --noop
    ```

=== "Windows (PowerShell)"

    ```powershell
    .venv\Scripts\Activate.ps1
    cibmt --noop
    ```

## Starting the application

```bash
uv run cibmt
```

Or the long name: `uv run cibmangotree`.

On a normal desktop install the app opens in a **native window** (NiceGUI). In **GitHub Codespaces** it serves in the browser on port 8000 instead.

## Project storage

Data directories are created automatically on first run via `platformdirs` (no manual database setup).

=== "macOS"

    `~/Library/Application Support/CIB Mango Tree/`

=== "Windows"

    `%LOCALAPPDATA%\Civic Tech DC\CIB Mango Tree\`

=== "Linux"

    `~/.local/share/CIB Mango Tree/`

| Storage | Role |
| --- | --- |
| TinyDB (`db.json`) | Project and analysis metadata |
| Project folders | Per-project files under the data directory |
| Parquet | Analysis inputs and outputs |

## Building an executable

For release-style packaging (not required for day-to-day development):

```bash
uv run pyinstaller pyinstaller.spec
```

Output is under `dist/` (`cibmangotree.app`, `cibmangotree.exe`, or a Linux binary depending on platform). `pyinstaller` comes from the `dev` dependency group.

## Troubleshooting

### Dependency install fails (often PyArrow)

Use **Python 3.12.x**. Other Python versions commonly break wheels such as PyArrow. Recreate the environment with 3.12 and run `uv sync --group dev` again.

### `cibmt: command not found`

Use `uv run cibmt`, or activate `.venv` first so scripts on that environment’s `bin`/`Scripts` path are available.

## Next steps

When the app starts cleanly, continue with the [GitHub Contributor Workflow](../contributing/github_workflow.md).
