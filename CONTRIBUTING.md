# Contributing

Thanks for considering a contribution to CImageOptimizer.

## Getting set up

```powershell
git clone https://github.com/MithunKiet/windows-image-optimizer.git
cd windows-image-optimizer
pip install -r requirements-dev.txt
python main.py        # run the app
python -m pytest       # run the test suite
```

## Project layout

See [ARCHITECTURE.md](ARCHITECTURE.md) before making structural changes -
it explains the `core` / `application` / `infrastructure` / `presentation`
split and why `main.py` stays outside the `cimageoptimizer/` package.

## Making a change

1. Open an issue first for anything beyond a small fix, so we can agree on
   the approach before you invest time.
2. Keep changes focused. Prefer several small, reviewable commits/PRs over
   one large one.
3. Add or update tests under `tests/` for any behavior change in
   `cimageoptimizer/core` or `cimageoptimizer/application`. The GUI
   (`presentation/gui`) is deliberately thin and delegates to those layers
   so that most logic can be tested without Tkinter.
4. Run `python -m pytest` before opening a PR.
5. If you touch `installer/` or `main.py`, do a manual smoke test:
   `python main.py`, then `pyinstaller --noconsole --onefile main.py`, then
   `installer\build-installer.ps1`, and confirm the resulting installer
   still installs/uninstalls cleanly.

## Code style

- Follow the existing style (see `.editorconfig`): 4-space indentation,
  type hints on public functions/methods, docstrings only where the *why*
  isn't obvious from the code.
- Don't add abstractions (interfaces, DI containers, config schemas) that
  aren't needed by the change at hand - see "What was intentionally left
  out" in ARCHITECTURE.md.

## Commit messages

Use an imperative summary line (`fix: ...`, `feat: ...`, `refactor: ...`,
`docs: ...`, `test: ...`, `chore: ...`) and explain *why* in the body when
the reasoning isn't obvious from the diff.

## Reporting bugs / requesting features

Please use the issue templates under `.github/ISSUE_TEMPLATE/`. For
anything security-related, see [SECURITY.md](SECURITY.md) instead of
filing a public issue.
