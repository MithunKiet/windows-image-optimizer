# Architecture

CImageOptimizer is a small Windows desktop app: a Tkinter GUI drives a batch
image-optimization pipeline. The code is organized into four layers, inspired
by Clean Architecture but kept intentionally lightweight for a project this
size - there is no dependency-injection container, no repository interfaces
for a database that doesn't exist, and no plugin system. The goal is
separation of concerns and testability, not ceremony.

```text
cimageoptimizer/
|-- core/                 # Dataclasses, enums, constants, exceptions. No I/O, no dependencies
|                          # on the other layers. Safe to import from anywhere.
|-- application/services/ # Business logic: discovery, compression, orchestration, reporting.
|                          # Depends only on core + infrastructure interfaces (functions).
|-- infrastructure/       # Concrete I/O: filesystem helpers, logging setup, settings.json.
`-- presentation/gui/     # Tkinter App. Depends on application services; nothing depends on it.
```

`main.py` stays at the repository root rather than inside the package. This
is a deliberate deviation from a strict `src/` layout: it lets
`python main.py` and `pyinstaller --noconsole --onefile main.py` keep working
with zero packaging/`sys.path` setup, because `cimageoptimizer/` is simply a
sibling importable package. Adding a `src/` layout would require an editable
install step before either command works, for no benefit in a single-app
repository that nothing else imports.

## Data flow

1. `presentation/gui/app.py`'s `App` reads user input (source folder *or* an
   explicit file selection, output folder, process mode, profile, and the
   resolution/overwrite/conversion checkboxes) and turns it into an
   `OptimizationSettings` (`core/models.py`), using
   `OptimizationSettings.for_profile()` to apply a Safe/Recommended/Advanced
   preset (`core/constants.py::PROFILE_PRESETS`).
2. It runs `OptimizationService.run()` (`application/services/optimization_service.py`)
   on a background thread, passing progress/log/cancel callbacks so the UI
   thread never blocks.
3. `OptimizationService` asks `FileDiscoveryService` which files are missing
   from `output_dir` - either by walking `source_dir`, or, when
   `settings.source_files` is set, from that explicit list instead (each
   written flat into `output_dir` by filename, since an arbitrary selection
   has no common directory structure worth preserving). This "missing"
   check is what makes reruns incremental, unless `overwrite_existing` is
   set.
4. Files are processed concurrently via a thread pool, each going through
   `ImageCompressionService`. It copies small files and non-images
   unchanged; for large images it optionally resizes (skipped entirely if
   `preserve_resolution`), then compresses using one of two strategies
   depending on format:
   - **Quality-controllable** (JPEG, WEBP - `QUALITY_CONTROLLABLE_EXTENSIONS`
     in `core/constants.py`): iterative quality search, stepping down until
     under `max_size_mb` or the profile's quality floor.
   - **Lossless** (PNG, BMP, TIFF, other): Pillow's `quality` parameter has
     no effect on these formats (verified directly - identical byte output
     at every quality value), so looping it would just re-encode the same
     bytes repeatedly. These get exactly one optimized pass. If still over
     `max_size_mb` and `convert_to_jpeg_if_oversized` is set, the file is
     re-saved as a real lossy `.jpg` and the lossless attempt is discarded.

   `ImageCompressionService.process()` returns the path actually written
   (normally `dst_file`, but the renamed `.jpg` when conversion happens), so
   downstream size/report data always reflects the real output file.
5. Each file's outcome (paths, sizes, success/failure) is aggregated into an
   `OptimizationResult`. On completion, the GUI can hand that result to
   `ReportService` (`application/services/report_service.py`) to write a
   JSON or CSV report.

## Why services instead of one big function

The original implementation was a single ~90-line function doing discovery,
per-file dispatch, resizing, quality search, and failure logging all inline.
Splitting it into `FileDiscoveryService`, `ImageCompressionService`, and
`OptimizationService` means each piece can be unit-tested in isolation
(see `tests/`) without spinning up Tkinter, and each has one reason to
change: discovery logic, compression logic, and orchestration/reporting
logic no longer have to be edited in the same place.

## Concurrency model

Files are processed with `concurrent.futures.ThreadPoolExecutor`
(`OptimizationService`, default `min(8, cpu_count)` workers). Each file is an
independent read/transform/write with no shared mutable state; the only
cross-thread state is result aggregation (`OptimizationResult.outcomes`),
which is protected by a lock. Cancellation is cooperative: once the cancel
callback returns `True`, no new file starts, but files already dispatched to
a worker finish normally.

## Settings persistence

`infrastructure/config.py` reads/writes a small `settings.json` under
`%APPDATA%\CImageOptimizer\` (last-used source/output folders, process mode,
profile, and the resolution/overwrite/conversion checkboxes). It's a plain
dict on disk, not a schema-versioned config system - appropriate for a
handful of fields that only affect UI defaults, not for correctness-critical
configuration. Individual file selections are deliberately not persisted,
since the files may no longer exist on the next launch.

## What was intentionally left out

- No dependency-injection container: every service takes its collaborators
  as constructor arguments with sensible defaults, which is enough for a
  dependency graph this shallow.
- No repository/DTO layer for a database: there is no database.
- No plugin/extension system: not asked for, and nothing in this codebase
  needs runtime extensibility.
