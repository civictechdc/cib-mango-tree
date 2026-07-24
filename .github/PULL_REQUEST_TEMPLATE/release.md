---
name: Release
about: Create a release PR
title: "Release v"
labels: release
---

## Release Checklist

### Version Management

- [ ] `pyproject.toml` version is updated correctly
- [ ] `uv.lock` is up to date (`uv lock`)
- [ ] `pylock.toml` is regenerated (`uv export -o pylock.toml`)

### Security Audit

- [ ] `uv run pip-audit` run locally with no unresolved vulnerabilities
- [ ] Any CVEs identified and addressed (or documented with justification)
- [ ] `pnpm audit` run in `src/cibmangotree/gui/` — check for and address any reported CVEs
- [ ] Check Dependabot alerts for any open JavaScript/Python vulnerabilities

<details>
<summary>Addressing pnpm CVEs</summary>

1. Identify vulnerabilities:
   ```bash
   cd src/cibmangotree/gui/
   pnpm audit
   ```
2. Update `package.json` version constraints for affected packages (if the fix is outside current semver ranges)
3. Update dependencies to latest versions within semver ranges:
   ```bash
   pnpm update
   ```
4. Rebuild the GUI components:
   ```bash
   pnpm build
   ```
5. Verify and commit:
   - Run `pnpm audit` again to confirm CVEs are resolved
   - Commit updated `package.json`, `pnpm-lock.yaml`,  
   - Check that `components/dist/UploadButton.js` has been regenerated(run `ls -l components/dist/UploadButton.js`), commit if need be  

</details>

<details>
<summary>Addressing Python CVEs</summary>

1. Identify vulnerabilities:
   ```bash
   uv run pip-audit
   ```
2. Update `pyproject.toml` version constraints for affected packages (if the fix is outside current semver ranges)
3. Regenerate lockfiles:
   ```bash
   uv lock
   uv export -o pylock.toml
   ```
4. Verify and commit:
   - Run `uv run pip-audit` again to confirm CVEs are resolved
   - Commit updated `pyproject.toml`, `uv.lock`, and `pylock.toml`

</details>

### Documentation

- [ ] `CHANGELOG.md`: rename `[Unreleased]` to `[<version>] - YYYY-MM-DD`, add new empty `[Unreleased]` section above it
- [ ] Release notes drafted for GitHub release (copy from `CHANGELOG.md` section)

### Testing

- [ ] All tests pass (`uv run pytest`)
- [ ] GUI builds successfully on all platforms (Windows, macOS x86, macOS arm64)

### Final Checks

- [ ] Git tag will be created after merge: `git tag v<version> && git push upstream v<version>`

---

## Changes in this Release

<!-- Summarize the key changes, features, and fixes -->

### New Features

-

### Bug Fixes

-

### Breaking Changes

-
