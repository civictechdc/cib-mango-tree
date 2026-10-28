# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [v0.14.0] - 2026-10-28

### Added

- Allow copying text from the n-gram data viewer table ([#424](https://github.com/civictechdc/cib-mango-tree/pull/424))
- Let users map a timestamp column when none is detected as datetime ([#423](https://github.com/civictechdc/cib-mango-tree/pull/423))
- Show how the hashtag time window slices posts before analysis runs ([#422](https://github.com/civictechdc/cib-mango-tree/pull/422))
- Drop shorter n-grams that only repeat inside a longer phrase ([#421](https://github.com/civictechdc/cib-mango-tree/pull/421))
- End-to-end tests that record the current GUI as a baseline ([#419](https://github.com/civictechdc/cib-mango-tree/pull/419))
- Linux (Debian) GUI build in CI ([#415](https://github.com/civictechdc/cib-mango-tree/pull/415))
- N-grams popup ([#407](https://github.com/civictechdc/cib-mango-tree/pull/407))
- Centralized GUI style abstraction layer ([#402](https://github.com/civictechdc/cib-mango-tree/pull/402), [#414](https://github.com/civictechdc/cib-mango-tree/pull/414))
- Synthetic / demo data CSV file ([#404](https://github.com/civictechdc/cib-mango-tree/pull/404))

### Changed

- Stop painting cancel buttons the same red as Delete ([#418](https://github.com/civictechdc/cib-mango-tree/pull/418))
- Improve release checklist (`release.md`): align with CI (`pip-audit --skip-editable`, Debian/Linux platforms), clarify CVE and Dependabot steps, remove duplicate playbooks

### Removed

- Dead code sweep ([#420](https://github.com/civictechdc/cib-mango-tree/pull/420))
- AI assistant infra/docs leftovers ([#410](https://github.com/civictechdc/cib-mango-tree/pull/410), [#413](https://github.com/civictechdc/cib-mango-tree/pull/413), [#406](https://github.com/civictechdc/cib-mango-tree/pull/406))

### Security

- Upgrade Python dependencies to clear `pip-audit` findings (including `aiohttp`, `filelock`, `urllib3`, `black`, and related lockfile updates)
- Upgrade GUI JS dependencies (including `vite`) to clear `pnpm audit` findings

## [v0.13.0] - 2026-09-21

### Changed

- Version bump and dependency updates for MSIX / Microsoft Store release workflow testing ([#405](https://github.com/civictechdc/cib-mango-tree/pull/405))

### Security

- Bump Python and JS dependencies for known CVEs as part of the 0.13.0 release path ([#405](https://github.com/civictechdc/cib-mango-tree/pull/405))

## [v0.12.0] - 2026-07-24

### Added

- Add `CHANGELOG.md` and release checklist `release.md` by [@KristijanArmeni]
- Add `profiling.md` to docs by [@nrposner] & [@KristijanArmeni]

### Changed

- Improved ngram analysis runtime by [@nrposner]
- Change the back/cancel buttons to red by [@KristijanArmeni]
- Add notification button when project is created by [@KristijanArmeni]
- Enable sorting in the project overview grid by [@KristijanArmeni]
- Fix version setting in pyinstaller.spec (MacOS) and GUI footer by [@KristijanArmeni]  
- Update JavaScript dependencies to address CVEs in rollup, picomatch, and postcss by [@KristijanArmeni]  

### Removed

- Cleanup dead code around project_select.py by [@KristijanArmeni]

### Fixed

- Add missing dependencies when running on Linux by [@llotenberg]

[@KristijanArmeni]: https://github.com/KristijanArmeni
[@nrposner]: https://github.com/nrposner
[@llotenberg]: https://github.com/llotenberg

[Unreleased]: https://github.com/civictechdc/cib-mango-tree/compare/v0.14.0...HEAD
[v0.14.0]: https://github.com/civictechdc/cib-mango-tree/compare/v0.13.0...v0.14.0
[v0.13.0]: https://github.com/civictechdc/cib-mango-tree/compare/v0.12.0...v0.13.0
[v0.12.0]: https://github.com/civictechdc/cib-mango-tree/compare/v0.11.0...v0.12.0
