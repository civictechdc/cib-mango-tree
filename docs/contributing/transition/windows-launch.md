# Windows launch

## Already merged

- Mark-of-the-Web removal (#346). `_remove_motw()`
  (`src/cibmangotree/gui/utils.py:39`) is called on Windows from `__main__.py`.
  This addresses the silent no-window failure in #324, where Windows blocked
  `Python.Runtime.dll` after the ZIP was extracted.
- Release pipeline (#350). The duplicate release workflow was removed.
  `release.yml` is now the single tag-triggered workflow and calls
  `build_gui.yml`. The v0.11.0-alpha release build, including the Windows
  `--noop` smoke test, passed.

These are done. The earlier idea of a release-workflow collision and a console
window on Windows no longer applies; `pyinstaller.spec` already sets
`console=False` on the Windows branch.

## Open work

### 1. Gate browser mode for Windows

`src/cibmangotree/gui/main_workflow.py:115` calls `ui.run(native=True, ...)`
unconditionally. The native window depends on the pywebview backend, which is the
component that fails on Windows when its DLLs are blocked. The maintainers settled
on browser mode as the Windows fallback in #324: the app serves its pages to the
default browser instead of a native window, which several users confirmed works.

Select the mode by platform, with `native=False` on Windows and `native=True`
elsewhere, and allow an environment variable to override it for testing. This
makes the documented fallback the default rather than a manual step, and keeps
macOS on the native window.

### 2. Correct the Mark-of-the-Web import

`__main__.py:21` reads `from src.cibmangotree.gui.utils import _remove_motw`.
Every other import in the file uses `cibmangotree.`, and the package installs
under that name (`pyproject.toml`, `where = ["src"]`). This is the only
`src.`-prefixed import in the tree. The PyInstaller build tolerates it because
`src` resolves during analysis, so the shipped executable is not affected, but a
source or wheel install on Windows fails at startup. Change it to
`from cibmangotree.gui.utils import _remove_motw`. This is the same class of
mistake as #338.

### 3. Clear the debug flag in the spec

`pyinstaller.spec:117` sets `debug=True` on the Windows and Linux branch; the
macOS branch uses `debug=False`. Set it to `False` so release builds are not
verbose.

## Larger follow-ups

- Windows code signing. Builds are unsigned, so users meet a SmartScreen warning
  (#224). Signing needs a certificate and CI secrets that do not exist yet. Track
  separately.
- An installer. An Inno Setup installer would remove the Mark of the Web at
  install time and avoid the long-path extraction problem one user hit with the
  built-in ZIP tool (#324). The maintainers pointed to Inno Setup and the mnelab
  project as a reference. Worth its own issue.
- Linux build (#246), which the maintainers placed below the Windows work.

## References

#324, #224, #346, #350; `main_workflow.py`, `__main__.py`, `pyinstaller.spec`.
