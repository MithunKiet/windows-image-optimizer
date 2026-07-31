# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Layered application structure under `cimageoptimizer/` (`core`,
  `application/services`, `infrastructure`, `presentation/gui`), replacing
  the previous `optimizer.py` + `main.py` split.
- Safe / Recommended / Advanced optimization profiles. Recommended
  reproduces the original hardcoded thresholds exactly, so existing
  behavior is unchanged by default.
- Concurrent file processing via a bounded thread pool.
- JSON/CSV optimization report export, available from the GUI after a run
  completes.
- Persisted user settings (`settings.json` under `%APPDATA%`): last-used
  source/output folders, process mode, and profile.
- Select individual files as the source, instead of always requiring a
  whole folder ("Or Select Individual Files..." in the GUI). Selected
  files are written flat into the output folder by filename.
- "Keep original resolution (don't resize, only compress)" option: skips
  the resize step entirely and only reduces file size via JPEG quality.
- "Overwrite existing files in output" option: disables the incremental
  skip-if-exists check so a rerun into a folder that already has a
  same-named file actually reprocesses it, instead of silently finding
  0 files to process.
- pytest suite covering discovery, compression, orchestration, profiles,
  settings persistence, report export, individual-file selection,
  resolution preservation, and overwrite behavior (32 tests).
- GitHub Actions CI: tests on Python 3.10-3.12, plus a packaging sanity
  build (PyInstaller + installer) on every push/PR to `main`.
- `LICENSE` (MIT), `.editorconfig`, `ARCHITECTURE.md`, `CONTRIBUTING.md`,
  `SECURITY.md`, `BUILD.md`, this changelog.

### Changed

- Dependencies in `requirements.txt` are now version-pinned for
  reproducible builds.

### Fixed

- The log panel's grid row weight was applied to the wrong row (row 6,
  which held nothing, instead of the log panel's row), so it never
  actually expanded when the window was resized.
- A file that failed both compression and its fallback copy was recorded
  as two separate failures instead of one, silently double-counting it in
  `failed_count` and the failed-files log.

### Removed

- `find_largest_image.py` - a one-off script with hardcoded personal paths
  and a hardcoded target date, disconnected from the rest of the app.
