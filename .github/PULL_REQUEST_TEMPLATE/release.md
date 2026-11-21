---
name: Release
about: Create a release PR
title: "Release v"
labels: release
---

## Release prep

Follow the full maintainer runbook: **[Release Checklist (wiki)](https://github.com/civictechdc/cib-mango-tree/wiki/Release-Checklist)**.

This PR should only contain the release-prep commits (version, lockfiles, changelog). After merge, push the version tag per the wiki.

### Before merge

- [ ] Release Checklist completed through local tests
- [ ] CI green (including GUI builds for Windows, macOS x86, macOS arm64, and Debian/Linux)

---

## Changelog for this release

Paste the matching version section from `CHANGELOG.md` below (same text for the GitHub Release notes later).
