# Security Policy

## Reporting a vulnerability

Please email **mithunkiet@gmail.com** with details instead of opening a
public issue. Include steps to reproduce and the potential impact. We'll
acknowledge reports as soon as possible.

## Scope and known design tradeoffs

CImageOptimizer is a single-user, unprivileged desktop tool: it reads image
files from a folder you choose and writes optimized copies to another folder
you choose. It does not run elevated, does not open network ports, and does
not phone home.

A few things worth knowing if you're auditing this codebase:

- **PowerShell execution policy bypass**: `installer/build-installer.ps1`,
  `installer/Uninstall-CImageOptimizer.ps1`, and the installer's shortcut
  creation (`Setup.cs`) all invoke `powershell.exe` with
  `-ExecutionPolicy Bypass`. This is standard practice for a self-contained
  installer that shouldn't depend on the target machine's execution policy,
  not a way to run untrusted code - the scripts involved are the ones
  shipped in this repository.
- **Temp script for shortcut creation**: `Setup.cs` writes a short PowerShell
  script to `%TEMP%` to create `.lnk` shortcuts via `WScript.Shell`, then
  deletes it. On a shared machine, a local attacker with write access to
  your temp folder during that narrow window could theoretically tamper
  with it; this is a low-severity, local-only concern given the installer
  itself runs unprivileged and unelevated.
- **Uninstaller swallows errors**: `Uninstall-CImageOptimizer.ps1` runs with
  `$ErrorActionPreference = "SilentlyContinue"`, so a failed deletion (e.g.
  a locked file) fails silently rather than surfacing to the user. This is
  a robustness/UX issue, not a security one, but is worth knowing if an
  uninstall appears to "succeed" while leaving files behind.
- **No path-collision guard**: the app doesn't currently prevent selecting an
  output directory that is inside (or equal to) the source directory. Doing
  so won't corrupt data - the optimizer only ever writes files that don't
  already exist at the destination path - but it can produce confusing
  results (the tool "optimizing its own output" on a second run). Treat this
  as a correctness caveat rather than a vulnerability.

## Supported versions

Only the latest commit on `main` is supported. There is no long-term
maintenance branch.
