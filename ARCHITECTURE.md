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

1. `presentation/gui/app.py`'s `App` reads user input (source/output folders,
   process mode, profile) and turns it into an `OptimizationSettings`
   (`core/models.py`), using `OptimizationSettings.for_profile()` to apply a
   Safe/Recommended/Advanced preset (`core/constants.py::PROFILE_PRESETS`).
2. It runs `OptimizationService.run()` (`application/services/optimization_service.py`)
   on a background thread, passing progress/log/cancel callbacks so the UI
   thread never blocks.
3. `OptimizationService` asks `FileDiscoveryService` which files under
   `source_dir` are missing from `output_dir` (this is what makes reruns
   incremental), then processes them concurrently via a thread pool, each
   file going through `ImageCompressionService` (resize + iterative
   quality-search JPEG/PIL compression, or a straight copy for small files
   and non-images).
4. Each file's outcome (sizes, success/failure) is aggregated into an
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
profile). It's a plain dict on disk, not a schema-versioned config system -
appropriate for four fields that only affect UI defaults, not for
correctness-critical configuration.

## What was intentionally left out

- No dependency-injection container: every service takes its collaborators
  as constructor arguments with sensible defaults, which is enough for a
  dependency graph this shallow.
- No repository/DTO layer for a database: there is no database.
- No plugin/extension system: not asked for, and nothing in this codebase
  needs runtime extensibility.
