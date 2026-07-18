---
name: Release
about: Create a release PR
title: "Release v"
labels: release
---

## Release Checklist

### Version Management

- [ ] `pyproject.toml` version is updated correctly
- [ ] `VERSION` file is created/updated with the release version
- [ ] `uv.lock` is up to date (`uv lock`)
- [ ] `requirements.txt` is regenerated (`uv export --format requirements-txt > requirements.txt`)
- [ ] `requirements-dev.txt` is regenerated (`uv export --format requirements-txt --only dev > requirements-dev.txt`)
- [ ] `requirements-docs.txt` is regenerated (`uv export --format requirements-txt --only docs > requirements-docs.txt`)

### Security Audit

- [ ] `uv run pip-audit` run locally with no unresolved vulnerabilities
- [ ] Any CVEs identified and addressed (or documented with justification)
- [ ] `pnpm audit` run in `src/cibmangotree/gui/` — check for and address any reported CVEs
- [ ] Check Dependabot alerts for any open JavaScript/Python vulnerabilities

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
