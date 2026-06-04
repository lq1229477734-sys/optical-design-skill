import argparse
import json
import sys
from pathlib import Path


def candidate_roots():
    roots = []
    for base in [
        Path(r"D:\Program Files\ANSYS Inc"),
        Path(r"C:\Program Files\ANSYS Inc"),
        Path(r"C:\Program Files\Zemax OpticStudio"),
    ]:
        if base.is_dir():
            roots.extend(base.glob(r"**\Zemax OpticStudio"))
            roots.extend(base.glob(r"**\Ansys Zemax OpticStudio"))
    return roots


def resolve_root(zos_root):
    candidates = []
    if zos_root:
        candidates.append(Path(zos_root))
    candidates.extend(candidate_roots())

    seen = set()
    for root in candidates:
        root = root.expanduser()
        key = str(root).lower()
        if key in seen:
            continue
        seen.add(key)
        helper = root / "ZOSAPI_NetHelper.dll"
        zosapi = root / "ZOSAPI.dll"
        interfaces = root / "ZOSAPI_Interfaces.dll"
        if helper.exists() and zosapi.exists() and interfaces.exists():
            return root, helper, zosapi, interfaces
    return None, None, None, None


def run_standalone(root, helper, zosapi, interfaces):
    import clr
    import System

    sys.path.insert(0, str(root))
    clr.AddReference(str(helper))
    clr.AddReference(str(interfaces))
    clr.AddReference(str(zosapi))

    import ZOSAPI_NetHelper

    initialized = ZOSAPI_NetHelper.ZOSAPI_Initializer.Initialize(str(root))
    if not initialized:
        return {"standalone_status": "FAILED", "error": "ZOSAPI_Initializer.Initialize returned false"}

    import ZOSAPI

    connection = ZOSAPI.ZOSAPI_Connection()
    app = connection.CreateNewApplication()
    if app is None:
        return {"standalone_status": "FAILED", "error": "CreateNewApplication returned None"}

    result = {
        "standalone_status": "OK",
        "app_mode": str(getattr(app, "Mode", "unknown")),
        "is_valid_license": bool(getattr(app, "IsValidLicenseForAPI", False)),
        "has_primary_system": app.PrimarySystem is not None,
    }

    try:
        app.CloseApplication()
    except Exception as exc:
        result["close_warning"] = repr(exc)

    return result


def main():
    parser = argparse.ArgumentParser(description="Locate OpticStudio ZOS-API DLLs and optionally smoke-test Standalone mode.")
    parser.add_argument("--zos-root", help="OpticStudio install root containing ZOSAPI_NetHelper.dll")
    parser.add_argument("--standalone", action="store_true", help="Attempt CreateNewApplication() after locating DLLs")
    parser.add_argument("--json-out", help="Optional path for JSON status output")
    args = parser.parse_args()

    root, helper, zosapi, interfaces = resolve_root(args.zos_root)
    status = {
        "resolved": root is not None,
        "zos_root": str(root) if root else None,
        "helper": str(helper) if helper else None,
        "zosapi": str(zosapi) if zosapi else None,
        "interfaces": str(interfaces) if interfaces else None,
    }

    if root and args.standalone:
        try:
            status.update(run_standalone(root, helper, zosapi, interfaces))
        except Exception as exc:
            status.update({"standalone_status": "FAILED", "error": repr(exc)})

    text = json.dumps(status, indent=2)
    print(text)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n", encoding="utf-8")
    return 0 if status.get("resolved") else 2


if __name__ == "__main__":
    raise SystemExit(main())
