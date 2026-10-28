---
name: Release
about: Create a release PR
title: "Release v"
labels: release
---

## Release Checklist

You will make changes to some config-related files, which are then committed and merged via a release prep PR.

Once that PR is merged, you will create and push the version tag to finish the release.

**Remotes:** `origin` is typically your fork; `upstream` is `civictechdc/cib-mango-tree`. Pull the default branch from the remote you use to track upstream merges. Push the release tag to `upstream`.

**Version strings (pick one version, e.g. `0.14.0`, and keep these forms consistent):**

| Where                  | Form                  | Example                     |
| ---------------------- | --------------------- | --------------------------- |
| `pyproject.toml`       | no `v`                | `version = "0.14.0"`        |
| Branch name            | `release-v` + version | `release-v0.14.0`           |
| `CHANGELOG.md` heading | `v` + version         | `## [v0.14.0] - YYYY-MM-DD` |
| Git tag                | `v` + version         | `v0.14.0`                   |

### Start

Done when: local default branch matches the remote tip that should ship, and you are on a dedicated release branch.

- [ ] Ensure default branch includes **all merged PRs** that should ship in this release

```bash
git pull
```

- [ ] Create and check out a **dedicated release branch** from that tip. Do all remaining checklist work on this branch — not on the default branch

```bash
git checkout -b release-v<version>
```

### Version Management

Done when: `pyproject.toml` and lockfiles match the release version.

- [ ] Set the release version in `pyproject.toml`
  - Under `[project]`, change `version = "<current-version>"` to the version being released (e.g. `version = "0.14.0"`)
- [ ] Update `uv.lock`

```bash
uv lock
```

- [ ] Regenerate `pylock.toml`

```bash
uv export -o pylock.toml
```
(There will be a log dump in the terminal. This is normal.)

### Dependency CVE check

Done when: local `pip-audit` and `pnpm audit` are clean (or any left-open finding is documented later in the release prep PR).

- [ ] Run pip-audit locally with no unresolved vulnerabilities

```bash
uv run pip-audit --skip-editable
```

- [ ] If pip-audit reported vulnerabilities, fix them before continuing (or document later in the release prep PR why a finding is left open):
  - Raise minimum versions in `pyproject.toml` as needed
  - Update the lockfile (use `--upgrade-package <name>` when a specific package must move):

```bash
uv lock
# or: uv lock --upgrade-package <name>
```

  - Regenerate `pylock.toml`:

```bash
uv export -o pylock.toml
```

  - Re-run until clean (eg pip-audit returns "No known vulnerabilities found"):

```bash
uv run pip-audit --skip-editable
```

  - If upgrades do not land: `[tool.uv] exclude-newer` may be blocking newer fix releases — relax it temporarily, then restore after the lock updates
- [ ] Check for and address any reported CVEs in the GUI JS deps:
  - Prerequisite: `pnpm` on PATH (GUI pins `pnpm@10.7.0` in `package.json`). If missing:

```bash
corepack enable
corepack prepare pnpm@10.7.0 --activate
```

  - Do this:

```bash
cd src/cibmangotree/gui/
pnpm audit
pnpm update
```

  - If `pnpm audit` still reports CVEs after you ran `pnpm update`, edit `package.json` by hand:
    - Find the package name from the audit output
    - Set its version to at least the audit’s “Patched versions” minimum (example: audit says vite needs `>=7.3.7` → change `"vite": "^7.3.6"` to `"vite": "^7.3.7"`)
    - Save the file, then run:

```bash
pnpm update
pnpm build
pnpm audit
```

  - Repeat until `pnpm audit` is clean (eg pnpm audit returns "No known vulnerabilities found")
  - Return to the repo root before continuing (changelog, tests, git):

```bash
cd ../../../
```

- [ ] Check Dependabot alerts: https://github.com/civictechdc/cib-mango-tree/security/dependabot
  - Dependabot alerts refer to **code already merged** into the repo (default branch). They do **not** describe the new dependency fixes you are making in this release checklist until those changes are merged. A large open count is normal before the release PR merges.
  - If local `pip-audit --skip-editable` and `pnpm audit` are clean, you do **not** need to resolve every alert one-by-one before continuing.
  - Optional: skim **Critical/High** only for packages you did not already upgrade; otherwise treat remaining opens as expected to clear after merge.

### Release documentation / Changelog

Done when: `[Unreleased]` is renamed for this version and a new empty `[Unreleased]` section sits above it.

- [ ] Update `CHANGELOG.md`: rename `[Unreleased]` to `[v<version>] - YYYY-MM-DD` (example: `## [v0.14.0] - 2026-10-28`), add a new empty `[Unreleased]` section above it. This file is the project’s lasting history of what each version shipped; for the GitHub Release notes, copy the matching version section from here.

### Testing

Done when: the test suite passes locally.

- [ ] All tests pass

```bash
uv run pytest
```

### Merge release prep into the default branch, then publish

Done when: the release prep PR is merged, the tag is on `upstream`, and the GitHub Release / build workflow has started.

- [ ] Commit the release-prep changes on the dedicated release branch, push the branch, then open a pull request into the default branch with the **Release** template (paste the matching `CHANGELOG.md` section below)

```bash
git add .
git commit -m "Prepare release v<version>"
git push -u origin HEAD
```

  - Open the PR against `civictechdc/cib-mango-tree` `main` (compare across forks if needed). Choose the **Release** template. Example with `gh`:

```bash
gh pr create --repo civictechdc/cib-mango-tree --base main --title "Release v<version>"
```

- [ ] On the PR **Checks** tab, wait for CI checks to complete and confirm CI checks are green, including GUI builds for Windows, macOS x86, macOS arm64, and Debian/Linux (CI runs these; you only verify results)
- [ ] Merge that pull request when ready
- [ ] After merge, create and push the tag (this triggers the GitHub Release / build workflow)

```bash
git tag v<version>
git push upstream v<version>
```

---

## Changelog for this release

Paste the matching version section from `CHANGELOG.md` below (same text for the GitHub Release notes later).
