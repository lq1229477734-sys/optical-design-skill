#!/usr/bin/env python3
"""Open a Lumerical FDTD project and run an LSF script with lumapi."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def import_lumapi(root: str):
    api_dir = os.path.join(root, "api", "python")
    bin_dir = os.path.join(root, "bin")
    sys.path.insert(0, api_dir)
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(api_dir)
        os.add_dll_directory(bin_dir)
    import lumapi  # type: ignore

    return lumapi


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lumerical-root", default=os.environ.get("LUMERICAL_ROOT", r"D:\Program Files\ANSYS Inc\v252\Lumerical"))
    parser.add_argument("--project", required=True, help="Path to the .fsp project")
    parser.add_argument("--script", required=True, help="Path to the .lsf script")
    parser.add_argument("--visible", action="store_true", help="Open a visible FDTD session")
    parser.add_argument("--delete-output", action="append", default=[], help="File to delete before running; repeatable")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project = Path(args.project).resolve()
    script = Path(args.script).resolve()
    if not project.exists():
        raise FileNotFoundError(project)
    if not script.exists():
        raise FileNotFoundError(script)

    for output in args.delete_output:
        path = Path(output)
        if path.exists():
            path.unlink()

    lumapi = import_lumapi(args.lumerical_root)
    fdtd = lumapi.FDTD(filename=str(project), hide=not args.visible)
    try:
        fdtd.feval(str(script))
    finally:
        fdtd.close()

    print(f"Ran {script} on {project}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
