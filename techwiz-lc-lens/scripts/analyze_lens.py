"""Post-process TechWiz LCD 3D director results for a cylindrical LC lens.

The script reads TechWiz v15 binary mesh/director files, integrates the local
extraordinary index through the LC layer, fits a parabolic OPD profile, and
writes a summary plus per-voltage CSV/PNG files.

Run ``python analyze_lens.py --help`` for options. NumPy is required;
Matplotlib is optional and controls PNG generation only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np


MESH_HEADER_BYTES = 14
MESH_RECORD_BYTES = 56
DIRECTOR_HEADER_BYTES = 24
DIRECTOR_RECORD_BYTES = 28


@dataclass(frozen=True)
class Context:
    root: Path
    parameters_path: Path
    parameters: dict
    base_name: str
    project_name: str
    ne: float
    no: float
    wavelength_m: float
    pitch_m: float
    aperture_m: float
    gap_m: float


def load_context(project_dir: str | Path = ".", parameters_file: str | Path | None = None,
                 project_name: str | None = None) -> Context:
    root = Path(project_dir).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"project directory not found: {root}")
    if parameters_file:
        parameters_path = Path(parameters_file)
        if not parameters_path.is_absolute():
            parameters_path = root / parameters_path
    else:
        matches = sorted(root.glob("*_parameters.json"))
        if len(matches) != 1:
            raise ValueError(f"expected exactly one *_parameters.json in {root}; found {len(matches)}")
        parameters_path = matches[0]
    parameters = json.loads(parameters_path.read_text(encoding="utf-8"))
    base_name = parameters.get("project_name") or parameters_path.name.removesuffix("_parameters.json")
    required = ("pitch", "gap", "ne", "no")
    missing = [key for key in required if key not in parameters]
    if missing:
        raise ValueError("parameter file is missing: " + ", ".join(missing))
    pitch_um = float(parameters["pitch"])
    aperture_um = float(parameters.get("aperture", pitch_um - float(parameters.get("e_w", 0.0))))
    if not 0 < aperture_um <= pitch_um:
        raise ValueError(f"aperture must be in (0, pitch]; got {aperture_um} µm")
    ne, no = float(parameters["ne"]), float(parameters["no"])
    if not ne > no > 0:
        raise ValueError("parameters must satisfy ne > no > 0")
    return Context(
        root=root,
        parameters_path=parameters_path,
        parameters=parameters,
        base_name=base_name,
        project_name=project_name or base_name,
        ne=ne,
        no=no,
        wavelength_m=float(parameters.get("wavelength_nm", 550.0)) * 1e-9,
        pitch_m=pitch_um * 1e-6,
        aperture_m=aperture_um * 1e-6,
        gap_m=float(parameters["gap"]) * 1e-6,
    )


def _read_bytes(path: str | Path) -> bytes:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"TechWiz result file not found: {source}")
    return source.read_bytes()


def read_mesh(path: str | Path) -> np.ndarray:
    data = _read_bytes(path)
    if len(data) < MESH_HEADER_BYTES:
        raise ValueError(f"mesh file is shorter than its {MESH_HEADER_BYTES}-byte header: {path}")
    node_count = struct.unpack("<i", data[6:10])[0]
    if node_count <= 0:
        raise ValueError(f"mesh contains an invalid node count {node_count}: {path}")
    expected = MESH_HEADER_BYTES + MESH_RECORD_BYTES * node_count
    if len(data) < expected:
        raise ValueError(f"mesh file is truncated: expected at least {expected} bytes, got {len(data)}")
    record_type = np.dtype([("id", "<i4"), ("fields", "<f4", 13)])
    records = np.frombuffer(data, offset=MESH_HEADER_BYTES, count=node_count, dtype=record_type)
    xyz = records["fields"][:, :3].astype(float)
    if not np.isfinite(xyz).all():
        raise ValueError(f"mesh contains non-finite coordinates: {path}")
    return xyz


def read_director(path: str | Path, node_count: int) -> np.ndarray:
    data = _read_bytes(path)
    expected = DIRECTOR_HEADER_BYTES + DIRECTOR_RECORD_BYTES * node_count
    if len(data) < expected:
        raise ValueError(f"director file is truncated: expected at least {expected} bytes, got {len(data)}: {path}")
    result = np.frombuffer(data, dtype="<f4", count=node_count * 7, offset=DIRECTOR_HEADER_BYTES).reshape(node_count, 7).astype(float)
    if not np.isfinite(result).all():
        raise ValueError(f"director file contains non-finite values: {path}")
    return result


def profile(xyz: np.ndarray, director: np.ndarray, pitch: float, ne: float, no: float):
    if len(xyz) != len(director):
        raise ValueError(f"mesh/director node count mismatch: {len(xyz)} vs {len(director)}")
    lc_mask = np.linalg.norm(director[:, 1:4], axis=1) > 0.5
    if not lc_mask.any():
        raise ValueError("director result contains no valid LC nodes (|n| > 0.5)")
    x, z = xyz[lc_mask, 0], xyz[lc_mask, 2]
    if np.ptp(x) > pitch * 1.05:
        raise ValueError(f"mesh X span {np.ptp(x):.6g} m exceeds configured pitch {pitch:.6g} m")
    nz = np.clip(np.abs(director[lc_mask, 3]), 0, 1)
    neff = 1.0 / np.sqrt(nz**2 / no**2 + (1 - nz**2) / ne**2)
    z_values = np.unique(np.round(z, 10))
    x_values = np.unique(np.round(x, 10))
    if len(z_values) < 2 or len(x_values) < 3:
        raise ValueError("not enough distinct LC mesh coordinates for OPD integration and fitting")
    z_index = np.searchsorted(z_values, np.round(z, 10))
    x_index = np.searchsorted(x_values, np.round(x, 10))
    sums = np.zeros((len(z_values), len(x_values)), dtype=float)
    counts = np.zeros_like(sums)
    np.add.at(sums, (z_index, x_index), neff)
    np.add.at(counts, (z_index, x_index), 1)
    grid = sums / np.where(counts == 0, np.nan, counts)
    for column_index in range(grid.shape[1]):
        column = grid[:, column_index]
        valid = ~np.isnan(column)
        if valid.sum() >= 2:
            grid[:, column_index] = np.interp(z_values, z_values[valid], column[valid])
    complete = ~np.isnan(grid).any(axis=0)
    x_values, grid = x_values[complete], grid[:, complete]
    if len(x_values) < 3:
        raise ValueError("fewer than three complete X columns remain after filling the LC director grid")
    trapezoid = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    opd = trapezoid(grid - no, z_values, axis=0)
    thickness = z_values[-1] - z_values[0]
    if thickness <= 0:
        raise ValueError("LC mesh has zero or negative Z thickness")
    average_index = no + opd / thickness
    return x_values, average_index, opd


def fit_parabola(x_values: np.ndarray, opd: np.ndarray, aperture: float):
    aperture_mask = np.abs(x_values) <= aperture / 2 + 1e-15
    if aperture_mask.sum() < 3:
        raise ValueError(f"only {aperture_mask.sum()} X samples lie inside the configured aperture")
    matrix = np.vstack([np.ones(aperture_mask.sum()), x_values[aperture_mask] ** 2]).T
    coefficients, *_ = np.linalg.lstsq(matrix, opd[aperture_mask], rcond=None)
    model = matrix @ coefficients
    span = float(np.ptp(opd[aperture_mask]))
    rmse_opd = float(np.sqrt(np.mean((opd[aperture_mask] - model) ** 2)))
    rmse_normalized = rmse_opd / span if span > np.finfo(float).eps else math.nan
    focal_length = -1 / (2 * coefficients[1]) if abs(coefficients[1]) > np.finfo(float).tiny else math.inf
    return coefficients, aperture_mask, model, rmse_normalized, rmse_opd, focal_length


def select_voltage_files(root: Path, project_name: str):
    result_dir = root / "LC" / f"{project_name}_dat"
    if not result_dir.is_dir():
        raise FileNotFoundError(f"TechWiz voltage result directory not found: {result_dir}")
    pattern = re.compile(r"([+-]?[\d.]+)\[V\]_([\d.]+)\[ms\]\.dat$", re.IGNORECASE)
    selected = {}
    for path in result_dir.glob("*.dat"):
        match = pattern.search(path.name)
        if not match:
            continue
        voltage, time_ms = float(match.group(1)), float(match.group(2))
        candidate = (path.stat().st_mtime_ns, time_ms, path)
        if voltage not in selected or candidate[:2] > selected[voltage][:2]:
            selected[voltage] = candidate
    if not selected:
        raise FileNotFoundError(f"no voltage-tagged director .dat files found in {result_dir}")
    return {voltage: (time_ms, path) for voltage, (_, time_ms, path) in selected.items()}


def output_directory(context: Context) -> Path:
    if context.project_name == context.base_name:
        suffix = ""
    elif context.project_name.startswith(context.base_name + "_"):
        suffix = "_" + context.project_name[len(context.base_name) + 1:]
    else:
        suffix = "_" + context.project_name
    return context.root / ("LENS_ANALYSIS" + suffix)


def analyze(context: Context, make_plots: bool = True) -> Path:
    mesh_path = context.root / "LC" / f"{context.project_name}_MESH.dat"
    xyz = read_mesh(mesh_path)
    files = select_voltage_files(context.root, context.project_name)
    output = output_directory(context)
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    pyplot = None
    if make_plots:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as pyplot
        except ImportError:
            print("warning: Matplotlib is unavailable; CSV output will still be written", file=sys.stderr)

    for voltage in sorted(files):
        time_ms, path = files[voltage]
        director = read_director(path, len(xyz))
        x_values, average_index, opd = profile(xyz, director, context.pitch_m, context.ne, context.no)
        coefficients, aperture_mask, model, rmse_norm, rmse_opd, focal_length = fit_parabola(x_values, opd, context.aperture_m)
        opd_depth = float(np.ptp(opd[aperture_mask]))
        center_index = average_index[np.argmin(np.abs(x_values))]
        edge_values = np.where(aperture_mask)[0]
        edge_index = average_index[edge_values[np.argmax(np.abs(x_values[edge_values]))]]
        rows.append({
            "V": voltage, "t_ms": time_ms, "dOPD_nm": opd_depth * 1e9,
            "phase_waves": opd_depth / context.wavelength_m, "f_mm": focal_length * 1e3,
            "RMSE_normalized": rmse_norm, "RMSE_OPD_nm": rmse_opd * 1e9,
            "RMSE_neff": rmse_opd / context.gap_m, "n_center": center_index, "n_edge": edge_index,
        })
        fitted_full = coefficients[0] + coefficients[1] * x_values**2
        profile_path = output / f"profile_{voltage:05.2f}V.csv"
        with profile_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["x_um", "n_eff_avg", "dn_eff", "OPD_nm", "parabola_fit_OPD_nm"])
            for index, x_value in enumerate(x_values):
                writer.writerow([f"{x_value * 1e6:.9g}", f"{average_index[index]:.9g}",
                                 f"{opd[index] / context.gap_m:.9g}", f"{opd[index] * 1e9:.9g}",
                                 f"{fitted_full[index] * 1e9:.9g}" if aperture_mask[index] else ""])
        if pyplot:
            figure, axis = pyplot.subplots(figsize=(6, 4))
            axis.plot(x_values * 1e6, opd / context.gap_m, "o", ms=3, label="TechWiz LC result")
            axis.plot(x_values[aperture_mask] * 1e6, model / context.gap_m, "-", label="parabola fit")
            axis.set_xlabel("x [µm]")
            axis.set_ylabel("Δn_eff = <n_eff> - n_o")
            axis.set_title(f"{voltage:g} V  RMSE={rmse_opd / context.gap_m:.5f}  f={focal_length * 1e3:.2f} mm")
            axis.legend()
            figure.tight_layout()
            figure.savefig(output / f"profile_{voltage:05.2f}V.png", dpi=160)
            pyplot.close(figure)

    summary_path = output / "summary.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(summary_path)
    for row in rows:
        print(f"{row['V']:g} V: dOPD={row['dOPD_nm']:.2f} nm, f={row['f_mm']:.4f} mm, RMSE_norm={row['RMSE_normalized']:.6f}")
    return summary_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", nargs="?", default=".", help="TechWiz project directory")
    parser.add_argument("legacy_project_name", nargs="?", help=argparse.SUPPRESS)
    parser.add_argument("--project", help="project/result prefix; defaults to project_name in parameters JSON")
    parser.add_argument("--parameters", help="parameters JSON path, relative to project_dir unless absolute")
    parser.add_argument("--no-plots", action="store_true", help="skip optional PNG plots")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project_name = args.project or args.legacy_project_name
    try:
        context = load_context(args.project_dir, args.parameters, project_name)
        analyze(context, make_plots=not args.no_plots)
    except (OSError, ValueError, json.JSONDecodeError, struct.error) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
