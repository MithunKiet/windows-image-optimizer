# Build Guide

This expands on the README's step-by-step instructions with more detail on
what each command does and how CI verifies them.

## Prerequisites

- Windows (the GUI uses Tkinter's native Windows theming; the installer is
  Windows-only)
- Python 3.10+ on PATH
- A .NET Framework C# compiler, present on most Windows installs at
  `C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe` (or the
  non-64-bit path as a fallback)

## Dependency sets

- `requirements.txt` - runtime dependencies needed to run the app or build
  the exe/installer: Pillow, tqdm, pyinstaller.
- `requirements-dev.txt` - the above, plus `pytest`, for running the test
  suite.

```powershell
pip install -r requirements.txt        # to run or build the app
pip install -r requirements-dev.txt    # to also run tests
```

## Running from source

```powershell
python main.py
```

`main.py` is a thin launcher; the actual application lives in
`cimageoptimizer/` (see [ARCHITECTURE.md](ARCHITECTURE.md)).

## Running tests

```powershell
python -m pytest
```

The suite covers `cimageoptimizer/core` and `cimageoptimizer/application`
(discovery - including individual-file selection, compression - including
the quality-search vs. lossless-single-pass split and JPEG-conversion
fallback, orchestration, profiles, settings persistence, report export).
The GUI layer (`presentation/gui`) is intentionally thin and is exercised
manually rather than under pytest, since it's mostly Tkinter wiring with no
independent logic.

## Building the standalone EXE

```powershell
pyinstaller --noconsole --onefile main.py
```

Produces `dist\main.exe`. PyInstaller performs static import analysis
starting from `main.py`; because `cimageoptimizer/` is a normal sibling
package (not behind an editable install), it's picked up automatically -
no `--paths` or hidden-import flags are needed.

## Building the installer

Requires `dist\main.exe` to already exist.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\installer\build-installer.ps1
```

This compiles `installer/Setup.cs` directly with `csc.exe` (no `.csproj`/
MSBuild project - kept lightweight since it's a ~150-line installer, not a
standalone application), embedding `dist\main.exe` and the uninstall script
as assembly resources, and produces `dist\CImageOptimizer-Setup.exe`.

## Continuous Integration

`.github/workflows/build.yml` runs on every push/PR to `main`:

1. **test**: installs `requirements-dev.txt` and runs `pytest` on Python
   3.10, 3.11, and 3.12.
2. **build** (gated on `test` passing): runs the exact PyInstaller and
   installer-build commands above and uploads `main.exe` and
   `CImageOptimizer-Setup.exe` as workflow artifacts, so a packaging
   regression is caught in CI rather than at release time.

Both jobs run on `windows-latest` because Tkinter GUI construction and the
`csc.exe`-based installer build both require Windows.

## Cleaning build output

`build/`, `dist/`, `installer/payload/`, and `*.spec` are all generated and
gitignored. Safe to delete between builds:

```powershell
Remove-Item -Recurse -Force build, dist, installer\payload, *.spec -ErrorAction SilentlyContinue
```
