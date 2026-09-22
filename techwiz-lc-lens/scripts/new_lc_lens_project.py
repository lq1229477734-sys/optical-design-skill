"""Generate a TechWiz LCD 3D v15 planar LC-lens project.

The generator starts from a project that TechWiz has already opened
successfully. It creates the text-based structure, electrode, project, stack,
and optional signal files; TechWiz must still generate the mesh and solve the
LC/optical analyses.

Run ``python new_lc_lens_project.py --help`` for usage. The JSON schema and an
example are documented in ``../references/configuration.md``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path


REQUIRED_NUMBERS = (
    "pitch", "Ly", "gap", "glass", "ito", "pi", "ne", "no",
    "pretilt", "azimuth", "lc_layers", "mesh_len", "mesh_max",
    "time_final_s", "time_step_s", "data_out_step",
)
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


def write_crlf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_bytes(normalized.replace("\n", "\r\n").encode("utf-8"))


def f12(value: float) -> str:
    return f"{value:16.12f}"


def _number(config: dict, key: str, *, positive: bool = False) -> float:
    value = config.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{key!r} must be a number")
    if positive and value <= 0:
        raise ValueError(f"{key!r} must be > 0")
    return float(value)


def validate_config(config: dict) -> None:
    missing = [key for key in ("name", "material", "electrodes", *REQUIRED_NUMBERS) if key not in config]
    if missing:
        raise ValueError("missing required config keys: " + ", ".join(missing))

    name = config["name"]
    if not isinstance(name, str) or not SAFE_NAME.fullmatch(name):
        raise ValueError("name must contain only letters, digits, dot, underscore, or hyphen")
    if not isinstance(config["material"], str) or not config["material"].strip():
        raise ValueError("material must be a non-empty TechWiz material name")

    for key in ("pitch", "Ly", "gap", "glass", "ito", "pi", "ne", "no", "mesh_len", "mesh_max", "time_final_s", "time_step_s"):
        _number(config, key, positive=True)
    for key in ("pretilt", "azimuth"):
        _number(config, key)
    for key in ("lc_layers", "data_out_step"):
        value = _number(config, key, positive=True)
        if not value.is_integer():
            raise ValueError(f"{key!r} must be an integer")
    if config["ne"] <= config["no"]:
        raise ValueError("ne must be greater than no for this uniaxial LC model")
    if config["mesh_len"] > config["mesh_max"]:
        raise ValueError("mesh_len cannot exceed mesh_max")

    electrodes = config["electrodes"]
    if not isinstance(electrodes, list) or not electrodes:
        raise ValueError("electrodes must be a non-empty list")
    names: set[str] = set()
    drivers: list[str] = []
    half_pitch = config["pitch"] / 2
    for index, electrode in enumerate(electrodes, 1):
        if not isinstance(electrode, dict):
            raise ValueError(f"electrode {index} must be an object")
        electrode_name = electrode.get("name")
        if not isinstance(electrode_name, str) or not SAFE_NAME.fullmatch(electrode_name):
            raise ValueError(f"electrode {index} has an invalid name")
        if electrode_name == "BOT_COM" or electrode_name in names:
            raise ValueError(f"electrode name {electrode_name!r} is reserved or duplicated")
        names.add(electrode_name)
        width = electrode.get("width")
        if not isinstance(width, (int, float)) or width <= 0 or width > config["pitch"]:
            raise ValueError(f"electrode {electrode_name!r} width must be in (0, pitch]")
        centers = electrode.get("centers")
        if not isinstance(centers, list) or not centers:
            raise ValueError(f"electrode {electrode_name!r} centers must be a non-empty list")
        for center in centers:
            if not isinstance(center, (int, float)) or abs(center) > half_pitch + 1e-9:
                raise ValueError(f"electrode {electrode_name!r} center {center!r} is outside the periodic cell")

        kind = str(electrode.get("type", "")).upper()
        if kind not in {"DC", "SWEEP", "SIGNAL"}:
            raise ValueError(f"electrode {electrode_name!r} type must be DC, SWEEP, or SIGNAL")
        if kind == "DC":
            _number(electrode, "v")
        elif kind == "SWEEP":
            start = _number(electrode, "start")
            stop = _number(electrode, "stop")
            step = _number(electrode, "step", positive=True)
            if stop <= start or step > stop - start:
                raise ValueError(f"electrode {electrode_name!r} has an invalid sweep range")
            drivers.append(electrode_name)
        else:
            drivers.append(electrode_name)

    if len(drivers) != 1:
        raise ValueError(f"exactly one non-DC Main electrode is required; found {len(drivers)}")

    signal = config.get("signal")
    if signal is not None:
        if config.get("signal_electrode") != drivers[0]:
            raise ValueError("signal_electrode must name the same electrode used as the main driver")
        if not isinstance(signal, list) or len(signal) < 2:
            raise ValueError("signal must contain at least two [time_s, voltage_V] points")
        previous_time = -float("inf")
        for point in signal:
            if not isinstance(point, list) or len(point) != 2 or not all(isinstance(v, (int, float)) for v in point):
                raise ValueError("every signal point must be [time_s, voltage_V]")
            if point[0] <= previous_time:
                raise ValueError("signal times must be strictly increasing")
            previous_time = point[0]
        if signal[0][0] < 0:
            raise ValueError("signal times cannot be negative")


def build_polygons(config: dict):
    half_pitch, half_y = config["pitch"] / 2, config["Ly"] / 2
    polygons = [(-half_pitch, half_pitch)]
    groups = []
    for electrode in config["electrodes"]:
        polygon_ids = []
        for center in electrode["centers"]:
            x0 = max(center - electrode["width"] / 2, -half_pitch)
            x1 = min(center + electrode["width"] / 2, half_pitch)
            if x1 <= x0:
                raise ValueError(f"electrode {electrode['name']!r} is empty after periodic-cell clipping")
            polygons.append((x0, x1))
            polygon_ids.append(len(polygons))
        groups.append((electrode["name"], polygon_ids))
    return polygons, groups, half_pitch, half_y


def make_str(config: dict) -> str:
    polygons, groups, half_pitch, half_y = build_polygons(config)
    um = 1e-6
    nodes = []
    for x0, x1 in polygons:
        nodes.extend([(x0, -half_y), (x0, half_y), (x1, half_y), (x1, -half_y)])
    nodes.extend([(-half_pitch, -half_y), (-half_pitch, half_y), (half_pitch, half_y), (half_pitch, -half_y)])
    lines = ["VERSION 8", 'TITLE "Structure Definition Pro"', "STRUCTURE", "{",
             '\tCOORDINATES 2 "X" "Y"', f"\tNODES {len(nodes)}"]
    for index, (x, y) in enumerate(nodes, 1):
        lines.append(f"\t{index:<8d}{f12(x * um)}  {f12(y * um)} ")
    lines.append(f"\tPOLYGONS {len(polygons)}")
    for polygon_index in range(len(polygons)):
        ids = "".join(f"{4 * polygon_index + offset + 1:<9d}" for offset in range(4))
        lines.append(f"\tPOLYGON 4    {ids}")
    base = 4 * len(polygons)
    lines.append("\tSIMAREA 4    " + "".join(f"{base + offset + 1:<9d}" for offset in range(4)))
    lines.append("}")
    lines += ["LOCAL", "{", "\tLOCNODES 8"]
    for index, (x, y) in enumerate([(-half_pitch, -half_y), (-half_pitch, half_y), (half_pitch, half_y), (half_pitch, -half_y)] * 2, 1):
        lines.append(f"\t{index:<8d}{f12(x * um)}  {f12(y * um)} ")
    lines += ["\tLOCPOLYGONS 2",
              "\tLOCPOLYGON 4    1        2        3        4        ", "\tCONDITION", "\t{", "\t}",
              "\tLOCPOLYGON 4    5        6        7        8        ", "\tCONDITION", "\t{", "\t}", "}"]
    top_ids = [polygon_id for _, ids in groups for polygon_id in ids]

    def zone(name, material, material_type, thickness, substrate, mask, *, metal=False, lc=False):
        block = ["ZONE", "{", f'\tNAME "{name}"', f'\tMATERIAL "{material}"', f'\tMAT_TYPE "{material_type}"',
                 f"\tTHICKNESS {thickness * um:.9e}", "\tPLANAR      1", "\tDOP     1.00"]
        if metal:
            block += ["\tTAPER_TYPE  1", "\tTAPER_ANGLE 90.000000", "\tTAPER_ROUND  2"]
        block += ["\tMULTI_LAYER  1", f'\tSUBSTRATE "{substrate}"']
        if lc:
            block.append("\tHARDENING  0")
        mask_text = " ".join(f"{value:<4d}" for value in [len(mask), *mask]).rstrip() if mask else "0"
        block += ["\tMASK_TYPE 0", "\tMASK   " + mask_text + (" " if mask else "")]
        if lc:
            block += ["\tLOCMASK_TOP   1    2 ", "\tLOCMASK_BOT   1    1 "]
        block += ["\tGAP_POSITION   0.000000000000  0.000000000000", "}"]
        return block

    lines += zone("TOP_GLASS", "GLASS", "INSULATOR", config["glass"], "SUB", [])
    lines += zone("TOP_SEG_ITO", "ITO", "METAL", config["ito"], "", top_ids, metal=True)
    lines += zone("TOP_PI", "PI", "INSULATOR", config["pi"], "", [])
    lines += zone("LC_LENS", config["material"], "LC", config["gap"], "FILL", [], lc=True)
    lines += zone("BOT_PI", "PI", "INSULATOR", config["pi"], "", [])
    lines += zone("BOT_COM_ITO", "ITO", "METAL", config["ito"], "", [1], metal=True)
    lines += zone("BOT_GLASS", "GLASS", "INSULATOR", config["glass"], "SUB", [])
    for name, polygon_ids in [("BOT_COM", [1]), *groups]:
        lines += ["ELECTRODE", "{", f'\tNAME "{name}"',
                  "\tPOLYGON" + "".join(f"{value:>5d}" for value in [len(polygon_ids), *polygon_ids]), "}"]
    return "\n".join(lines) + "\n"


def make_elt(config: dict, override: dict | None = None) -> str:
    rows = [("BOT_COM", "DC", 0.0, 0.0, 0.0, 0.0)]
    for source in config["electrodes"]:
        electrode = dict(source, **(override or {}).get(source["name"], {}))
        kind = electrode["type"].upper()
        if kind == "SWEEP":
            rows.append((electrode["name"], "SWEEP(SATURATION)", 0.0, electrode["start"], electrode["stop"], electrode["step"]))
        elif kind == "SIGNAL":
            rows.append((electrode["name"], "SIGNAL", 0.0, 0.0, 0.0, 0.0))
        else:
            rows.append((electrode["name"], "DC", electrode["v"], 0.0, 0.0, 0.0))
    main_indexes = [index for index, row in enumerate(rows) if row[1] != "DC"]
    if len(main_indexes) != 1:
        raise ValueError(f"electrode table must have exactly one Main row; found {len(main_indexes)}")
    main_index = main_indexes[0]
    lines = ["VERSION 5", 'TITLE "Assigning Voltage Condition of Electrode"', "ELECTRODES", "{", "\tFIELD", "\t{",
             '\t\t"ID" "Name" "Function" "Link" "Voltage Type" "Voltage" "Signal" "Start" "Stop" "Step" "Main/Sub" ',
             "\t}", f"\tELECTRODE  {len(rows)}", "\t{"]
    for index, (name, kind, voltage, start, stop, step) in enumerate(rows):
        prefix = "\t\t" if index == 0 else " \t\t"
        main_sub = "Main" if index == main_index else "Sub"
        lines.append(f'{prefix}{index + 1:<8d}{chr(34) + name + chr(34):>9s} \tNA      \t0 \t{kind:<13s} '
                     f'\t{voltage:.6f} \t0 \t{start:.6f} \t{stop:.6f} \t{step:.6f} \t{main_sub}')
    lines += [" \t}", "}"]
    return "\n".join(lines) + "\n"


def make_prj(config: dict, template_project: Path, electrode_file: str, signal_db: str = "") -> str:
    text = template_project.read_text(encoding="utf-8", errors="strict").replace("\r\n", "\n")
    replacements = {
        r'MaterialDB\s+"[^"]*"': f'MaterialDB   \t"\\{config.get("material_db", "Material_LC_Lens.db")}"',
        r'LightSourceDB\s+"[^"]*"': f'LightSourceDB\t"\\{config.get("light_source_db", "LightSource.ldb")}"',
        r'SignalDB\s+"[^"]*"': f'SignalDB     \t"{signal_db}"',
        r'StrFile\s+"[^"]*"': f'StrFile      \t"\\LAYOUT\\{config["name"]}.str"',
        r'EltFile\s+"[^"]*"': f'EltFile       \t"\\INPUT\\{electrode_file}"',
        r'StkFile\s+"[^"]*"': f'StkFile       \t"\\{config["name"]}_InputPolarizer.stk"',
    }
    for pattern, replacement in replacements.items():
        text, count = re.subn(pattern, lambda _match, value=replacement: value, text, count=1)
        if count != 1:
            raise ValueError(f"template project is missing field matched by {pattern!r}")

    def replace_number(key: str, value: str) -> None:
        nonlocal text
        text, count = re.subn(rf"({re.escape(key)}\s+)[-0-9.eE+]+", lambda match: match.group(1) + value, text, count=1)
        if count != 1:
            raise ValueError(f"template project is missing numeric field {key!r}")

    replace_number("Mesh_Length", f'{config["mesh_len"] * 1e-6:.8e}')
    replace_number("Mesh_Length_Max", f'{config["mesh_max"] * 1e-6:.8e}')
    replace_number("TimeFinal", f'{config["time_final_s"]:.8e}')
    replace_number("TimeStep", f'{config["time_step_s"]:.8e}')
    text, count = re.subn(r"(DataOutStep\s+)\d+", lambda match: match.group(1) + str(int(config["data_out_step"])), text, count=1)
    if count != 1:
        raise ValueError("template project is missing DataOutStep")

    zones = [("TOP_GLASS", False), ("TOP_SEG_ITO", False), ("TOP_PI", False), ("LC_LENS", True),
             ("BOT_PI", False), ("BOT_COM_ITO", False), ("BOT_GLASS", False)]
    rows = []
    for zone_name, is_lc in zones:
        values = (config["pretilt"], config["azimuth"], config["pretilt"], config["azimuth"], int(config["lc_layers"])) if is_lc else (0, 0, 0, 0, 0)
        rows.append(f'\t\t\t{chr(34) + zone_name + chr(34):>16s} \t {values[0]:.6f} \t {values[1]:.6f} '
                    f'\t {values[2]:.6f} \t {values[3]:.6f} \t {values[4]}')
    text, count = re.subn(r"(Zones )\d+\n\t\t\{\n.*?\n\t\t\}",
                          lambda _match: "Zones 7\n\t\t{\n" + "\n".join(rows) + "\n\t\t}", text, count=1, flags=re.S)
    if count != 1:
        raise ValueError("template project does not contain the expected RUBBING Zones block")
    return text


STACK_TEMPLATE = '''VERSION 2
"Stack Structure for Optical Analysis of LC Cell"
{
\tField
\t{
\t\t"Name" "ID" "Thickness" "Theta" "Phi" "Psi" "Trans-Absorp" "Material ID"
\t}
\tStack
\t{
\t\t   "LC_Cell"\t1  0.00000000e+000  0.00000000e+000  0.00000000e+000  0.00000000e+000 1 1
\t\t "Polarizer"\t2  2.00000000e+002  0.00000000e+000  PHI  0.00000000e+000 0 3000
\t}
}
'''


def make_sdb(name: str, points: list[list[float]]) -> str:
    lines = ["Version 1", '"Signal database for TechWiz LCD"', "{", "\tData", "\t{", f'\t\t"{name}"', "\t\t{"]
    lines += [f"\t\t\tTime \t {time:.8E} \tVolt \t {voltage:.8E}" for time, voltage in points]
    lines += ["\t\t}", "\t}", "}"]
    return "\n".join(lines) + "\n"


OPEN_CMD = '''@echo off
setlocal
if not defined TECHWIZ_DIR set "TECHWIZ_DIR=C:\\Program Files (x86)\\TechWiz LCD 3D"
if not exist "%TECHWIZ_DIR%\\TechWizLCD.exe" (
  echo TechWizLCD.exe not found under "%TECHWIZ_DIR%".
  echo Set TECHWIZ_DIR to the TechWiz LCD 3D installation directory and retry.
  pause
  exit /b 1
)
if exist "%TECHWIZ_DIR%\\License\\licnese.dat" set "LM_LICENSE_FILE=%TECHWIZ_DIR%\\License\\licnese.dat"
cd /d "%~dp0"
start "" /D "%~dp0" "%TECHWIZ_DIR%\\TechWizLCD.exe" "%~dp0{PROJECT}"
'''


ANALYZE_CMD = '''@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_EXE=python"
if defined PYTHON set "PYTHON_EXE=%PYTHON%"
if exist "%LOCALAPPDATA%\\Python\\bin\\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\\Python\\bin\\python.exe"
"%PYTHON_EXE%" {SCRIPT}
if errorlevel 1 echo Analysis failed. Check the message above and your Python dependencies.
pause
'''


def choose_template_project(template_dir: Path, requested: str | None) -> Path:
    if requested:
        candidate = template_dir / requested
        if not candidate.is_file():
            raise FileNotFoundError(f"template project not found: {candidate}")
        return candidate
    preferred = template_dir / f"{template_dir.name}.prj"
    if preferred.is_file():
        return preferred
    candidates = sorted(path for path in template_dir.glob("*.prj") if "response" not in path.stem.lower())
    if len(candidates) != 1:
        raise ValueError("template directory must contain one non-response .prj, or set template_project")
    return candidates[0]


def infer_aperture(config: dict) -> float:
    if "aperture" in config:
        aperture = _number(config, "aperture", positive=True)
        if aperture > config["pitch"]:
            raise ValueError("aperture cannot exceed pitch")
        return aperture
    half_pitch = config["pitch"] / 2
    boundary_widths = [electrode["width"] for electrode in config["electrodes"]
                       if any(abs(abs(center) - half_pitch) <= 1e-9 for center in electrode["centers"])]
    return config["pitch"] - max(boundary_widths) if boundary_widths else config["pitch"]


def project_readme(config: dict, template: Path) -> str:
    return f"""# {config['name']}

Generated by `techwiz-lc-lens/scripts/new_lc_lens_project.py` from the validated template `{template}`.

## Run

1. Double-click `1_OPEN_PROJECT.cmd`.
2. Run Mesh Generation and verify X/Y periodic boundaries and the expected electrode count.
3. Run LC Analysis after checking `BOT_COM = DC 0` and that exactly one driver is `Main`.
4. Run `2_ANALYZE_LENS.cmd` after TechWiz has written the LC result files.
5. For a response project, open `{config['name']}_Response.prj`, run the time-domain analysis, then run `3_ANALYZE_RESPONSE.cmd`.

Units in the source JSON are micrometres, volts, seconds, and degrees. Do not treat generated files as solved results until the TechWiz runs complete successfully.
"""


def build_project(config_path: Path, template_arg: Path | None, output_arg: Path | None, force: bool) -> Path:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    validate_config(config)
    template_dir = template_arg or (Path(config["template_dir"]) if config.get("template_dir") else None)
    if template_dir is None and os.environ.get("TECHWIZ_TEMPLATE_DIR"):
        template_dir = Path(os.environ["TECHWIZ_TEMPLATE_DIR"])
    if template_dir is None:
        raise ValueError("set --template, template_dir, or TECHWIZ_TEMPLATE_DIR to a validated TechWiz project")
    template_dir = template_dir.expanduser().resolve()
    if not template_dir.is_dir():
        raise FileNotFoundError(f"template directory not found: {template_dir}")
    template_project = choose_template_project(template_dir, config.get("template_project"))

    output_dir = (output_arg or (Path(config["out_dir"]) if config.get("out_dir") else config_path.parent / config["name"])).expanduser().resolve()
    name = config["name"]
    generated_targets = [
        output_dir / "LAYOUT" / f"{name}.str", output_dir / "INPUT" / f"{name}_main.elt",
        output_dir / f"{name}.prj", output_dir / f"{name}_InputPolarizer.stk",
        output_dir / f"{name}_parameters.json", output_dir / "README_CN.md",
        output_dir / "1_OPEN_PROJECT.cmd", output_dir / "2_ANALYZE_LENS.cmd",
        output_dir / "analyze_lens.py", output_dir / "analyze_response.py",
    ]
    if config.get("signal"):
        generated_targets += [
            output_dir / f"{name}_Response.sdb", output_dir / f"{name}_Response.prj",
            output_dir / "INPUT" / f"{name}_Response.elt", output_dir / "3_ANALYZE_RESPONSE.cmd",
        ]
    existing = [path for path in generated_targets if path.exists()]
    if existing and not force:
        raise FileExistsError("refusing to overwrite generated files; pass --force after reviewing: " + ", ".join(map(str, existing)))

    material_source = template_dir / config.get("material_db", "Material_LC_Lens.db")
    light_source = template_dir / config.get("light_source_db", "LightSource.ldb")
    for source in (material_source, light_source):
        if not source.is_file():
            raise FileNotFoundError(f"required template asset not found: {source}")

    for directory in ("INPUT", "LAYOUT", "LC", "MESH", "OPTICS", "PANEL", "TFT"):
        target = output_dir / directory
        target.mkdir(parents=True, exist_ok=True)
        if directory not in {"INPUT", "LAYOUT"}:
            (target / "_keep.txt").write_text("keep folder\n", encoding="utf-8")
    for source in (material_source, light_source):
        target = output_dir / source.name
        if not target.exists():
            shutil.copy2(source, target)

    write_crlf(output_dir / "LAYOUT" / f"{name}.str", make_str(config))
    write_crlf(output_dir / "INPUT" / f"{name}_main.elt", make_elt(config))
    write_crlf(output_dir / f"{name}.prj", make_prj(config, template_project, f"{name}_main.elt"))
    phi = float(config.get("polarizer_absorb_phi", 0.0))
    write_crlf(output_dir / f"{name}_InputPolarizer.stk", STACK_TEMPLATE.replace("PHI", f"{phi:.8e}"))
    write_crlf(output_dir / "1_OPEN_PROJECT.cmd", OPEN_CMD.replace("{PROJECT}", f"{name}.prj"))
    write_crlf(output_dir / "2_ANALYZE_LENS.cmd", ANALYZE_CMD.replace("{SCRIPT}", "analyze_lens.py"))

    if config.get("signal"):
        response_config = dict(config, time_final_s=config["signal"][-1][0], data_out_step=config.get("resp_data_out_step", 10))
        write_crlf(output_dir / f"{name}_Response.sdb", make_sdb(config.get("signal_name", "LENS_STEP"), config["signal"]))
        override = {config["signal_electrode"]: {"type": "SIGNAL"}}
        write_crlf(output_dir / "INPUT" / f"{name}_Response.elt", make_elt(config, override))
        signal_path = str(output_dir / f"{name}_Response.sdb")
        write_crlf(output_dir / f"{name}_Response.prj", make_prj(response_config, template_project, f"{name}_Response.elt", signal_path))
        write_crlf(output_dir / "3_ANALYZE_RESPONSE.cmd", ANALYZE_CMD.replace("{SCRIPT}", "analyze_response.py"))

    script_dir = Path(__file__).resolve().parent
    for script_name in ("analyze_lens.py", "analyze_response.py"):
        source = script_dir / script_name
        if not source.is_file():
            raise FileNotFoundError(f"companion script not found: {source}")
        shutil.copy2(source, output_dir / script_name)

    parameters = {
        "schema_version": 2, "project_name": name, "pitch": config["pitch"], "Ly": config["Ly"],
        "gap": config["gap"], "aperture": infer_aperture(config), "ne": config["ne"], "no": config["no"],
        "wavelength_nm": config.get("wavelength_nm", 550.0), "pretilt": config["pretilt"],
        "azimuth": config["azimuth"], "glass": config["glass"], "ito": config["ito"], "pi": config["pi"],
        "electrodes": config["electrodes"],
    }
    if config.get("signal"):
        parameters["signal"] = config["signal"]
        parameters["signal_electrode"] = config["signal_electrode"]
    write_crlf(output_dir / f"{name}_parameters.json", json.dumps(parameters, indent=2, ensure_ascii=False) + "\n")
    write_crlf(output_dir / "README_CN.md", project_readme(config, template_project))
    return output_dir


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="JSON project configuration")
    parser.add_argument("--template", type=Path, help="validated TechWiz project directory")
    parser.add_argument("--output", type=Path, help="output project directory (overrides out_dir)")
    parser.add_argument("--force", action="store_true", help="overwrite known generated files in an existing output directory")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        output = build_project(args.config.resolve(), args.template, args.output, args.force)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"created TechWiz project: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
