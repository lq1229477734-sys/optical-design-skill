---
name: lumerical-fdtd-automation
description: Automate Ansys Lumerical FDTD workflows with lumapi, .fsp projects, .lsf scripts, parameter scans, and result extraction. Use when Codex needs to create or modify FDTD projects, run Lumerical scripts, debug API/session issues, generate fast scan scripts, export monitor data, parse transmission spectra, or package repeatable FDTD automation workflows on Windows.
---

# Lumerical FDTD Automation

## Core Workflow

1. Detect the installed Lumerical root before assuming paths.
   Common working layout on Windows 2025 R2:
   `D:\Program Files\ANSYS Inc\v252\Lumerical`.

2. Prefer Lumerical's bundled Python when `lumapi` launch succeeds from a normal user shell:
   `...\Lumerical\python-3.13.1\python.exe`.

3. Add both API and binary directories before importing `lumapi`:

```python
sys.path.insert(0, r"...\Lumerical\api\python")
os.add_dll_directory(r"...\Lumerical\api\python")
os.add_dll_directory(r"...\Lumerical\bin")
import lumapi
```

4. For existing `.fsp` files, use `lumapi.FDTD(filename=path, hide=True)` and run `.lsf` scripts with `fdtd.feval(script_path)`.

5. If direct API launch fails with `Failed to start messaging, check licenses...`, test outside the sandbox/agent environment. Do not assume the project or license is invalid until a normal PowerShell run has been tried.

6. For fragile or long Lumerical scripts, generate `.lsf` files and a small Python runner. Avoid complex `python -c` strings with many quoted Windows paths.

7. Export results into stable text/CSV/NPZ/PNG artifacts. Preserve raw signed `transmission()` values and add absolute-value columns when monitor orientation makes signs negative.

## Common Tasks

### Run an existing LSF against an FSP

Use `scripts/run_lsf_with_lumapi.py` when the task is "open this project, run this script, save outputs".

Example:

```powershell
& "D:\Program Files\ANSYS Inc\v252\Lumerical\python-3.13.1\python.exe" -B scripts\run_lsf_with_lumapi.py --project path\model.fsp --script path\scan.lsf
```

### Analyze a transmission scan TXT

Use `scripts/analyze_transmission_scan.py` for files with columns like:

```text
phase_deg thickness_m wavelength_nm transmission
```

It writes a CSV with raw and absolute transmission and a PNG spectrum plot.

### Generate faster scan scripts

When optimizing a slow `.lsf` parameter scan:

- Reduce dimensions first, for example one thickness instead of many thicknesses.
- Keep the original wavelength grid if comparability matters.
- Merge repeated code paths for `+90` and `-90` phase scans into a single loop over `phases`.
- Write one table with explicit columns instead of multiple ambiguous text files.
- Add `switchtolayout;` before modifying geometry or sources after opening a project with existing analysis data.
- Avoid `rm()` in `.lsf`; it is disabled in safe mode. Delete stale output files in Python before running the `.lsf`.

## Debugging Rules

- `Failed to start messaging, check licenses...`: often environment/session isolation, not necessarily a bad license. Try a normal PowerShell command and request elevated/unsandboxed execution if needed.
- `rm command is disabled in safe mode`: remove `rm()` from `.lsf`; delete outputs from the Python runner.
- `you cannot modify most simulation objects while in analysis mode`: add `switchtolayout;` before geometry/material/source edits.
- Negative `transmission()`: keep the raw sign and explain monitor normal direction; use `abs(transmission)` only for plotted power magnitude.
- Existing GUI windows are not automatically controllable by `lumapi`; `lumapi.FDTD()` starts or manages an API session.

## References

Read `references/fdtd-workflow-notes.md` when working on real FDTD automation, especially BP/hBN/MoO3 scans, `.fsp` duplication, safe-mode issues, and result interpretation.
