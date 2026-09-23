"""Analyze TechWiz Signal-mode LC-lens director results.

The metric is lens OPD depth across the configured aperture. Rise time is the
10%→90% crossing interval after switch-on; decay time is 90%→10% after
switch-off. Switching times are inferred from the generated parameters JSON or
can be supplied explicitly.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

import analyze_lens as lens


def infer_switch_times(signal_points) -> tuple[float, float]:
    """Return the start of the first rising and first later falling ramp, in ms."""
    if not signal_points or len(signal_points) < 4:
        raise ValueError("signal metadata needs at least four points to infer switch-on and switch-off")
    changes = []
    for previous, current in zip(signal_points, signal_points[1:]):
        t0, v0 = map(float, previous)
        t1, v1 = map(float, current)
        if v1 != v0:
            changes.append((t0 * 1000.0, v1 - v0, t1 * 1000.0))
    rising = next((change for change in changes if change[1] > 0), None)
    falling = next((change for change in changes if change[1] < 0 and rising and change[0] > rising[0]), None)
    if not rising or not falling:
        raise ValueError("could not infer one rising and one later falling edge from signal metadata")
    return rising[0], falling[0]


def response_project_name(context: lens.Context, requested: str | None) -> str:
    if requested:
        return requested
    candidates = [context.base_name + "_Response", context.base_name + "_11V_Response"]
    existing = [name for name in candidates if (context.root / f"{name}.prj").is_file() or (context.root / "LC" / f"{name}_MESH.dat").is_file()]
    if len(existing) == 1:
        return existing[0]
    if len(existing) > 1:
        raise ValueError("multiple response projects found; select one with --project")
    return context.base_name + "_Response"


def select_time_files(root: Path, project_name: str):
    result_dirs = sorted((root / "LC").glob(f"{project_name}*_dat"))
    result_dirs = [path for path in result_dirs if path.is_dir()]
    if not result_dirs:
        raise FileNotFoundError(f"no Signal-mode result directory found for {project_name!r} under {root / 'LC'}")
    pattern = re.compile(r"([\d.]+)\[ms\]\.dat$", re.IGNORECASE)
    selected = {}
    for result_dir in result_dirs:
        for path in result_dir.glob("*.dat"):
            match = pattern.search(path.name)
            if not match:
                continue
            time_ms = float(match.group(1))
            candidate = (path.stat().st_mtime_ns, path)
            if time_ms not in selected or candidate[0] > selected[time_ms][0]:
                selected[time_ms] = candidate
    if not selected:
        raise FileNotFoundError(f"no time-tagged director .dat files found for {project_name!r}")
    return [(time_ms, selected[time_ms][1]) for time_ms in sorted(selected)]


def crossing_time(times: np.ndarray, values: np.ndarray, start: float, stop: float,
                  level: float, rising: bool) -> float:
    mask = (times >= start) & (times <= stop)
    selected_times, selected_values = times[mask], values[mask]
    for index in range(1, len(selected_times)):
        before, after = selected_values[index - 1], selected_values[index]
        crossed = before < level <= after if rising else before > level >= after
        if crossed:
            if after == before:
                return float(selected_times[index])
            fraction = (level - before) / (after - before)
            return float(selected_times[index - 1] + fraction * (selected_times[index] - selected_times[index - 1]))
    return math.nan


def analyze(context: lens.Context, project_name: str, t_on_ms: float, t_off_ms: float,
            make_plot: bool = True) -> Path:
    if not 0 <= t_on_ms < t_off_ms:
        raise ValueError("switch times must satisfy 0 <= t_on_ms < t_off_ms")
    mesh_path = context.root / "LC" / f"{project_name}_MESH.dat"
    xyz = lens.read_mesh(mesh_path)
    files = select_time_files(context.root, project_name)
    rows = []
    for time_ms, path in files:
        director = lens.read_director(path, len(xyz))
        x_values, average_index, opd = lens.profile(xyz, director, context.pitch_m, context.ne, context.no)
        _, aperture_mask, _, _, rmse_opd, focal_length = lens.fit_parabola(x_values, opd, context.aperture_m)
        opd_depth = float(np.ptp(opd[aperture_mask]))
        center_index = average_index[np.argmin(np.abs(x_values))]
        rows.append((time_ms, opd_depth * 1e9, opd_depth / context.gap_m,
                     center_index - context.no, rmse_opd / context.gap_m, focal_length * 1e3))
    values = np.asarray(rows, dtype=float)
    times, depth_nm = values[:, 0], values[:, 1]
    if times[0] > t_on_ms or times[-1] <= t_off_ms:
        raise ValueError(f"result time span {times[0]:g}–{times[-1]:g} ms does not cover both switching events")

    baseline_window = times <= t_on_ms
    on_window_width = min(50.0, max(1.0, 0.1 * (t_off_ms - t_on_ms)))
    on_window = (times >= t_off_ms - on_window_width) & (times <= t_off_ms)
    final_window_width = min(50.0, max(1.0, 0.1 * (times[-1] - t_off_ms)))
    final_window = times >= times[-1] - final_window_width
    if not baseline_window.any() or not on_window.any() or not final_window.any():
        raise ValueError("insufficient samples in baseline, on-state, or final-state averaging windows")
    baseline = float(depth_nm[baseline_window].mean())
    on_state = float(depth_nm[on_window].mean())
    final_state = float(depth_nm[final_window].mean())
    if on_state <= baseline:
        raise ValueError(f"on-state OPD depth ({on_state:.3g} nm) does not exceed baseline ({baseline:.3g} nm)")

    rise_10 = crossing_time(times, depth_nm, t_on_ms, t_off_ms, baseline + 0.1 * (on_state - baseline), True)
    rise_90 = crossing_time(times, depth_nm, t_on_ms, t_off_ms, baseline + 0.9 * (on_state - baseline), True)
    decay_90 = crossing_time(times, depth_nm, t_off_ms, times[-1], final_state + 0.9 * (on_state - final_state), False)
    decay_10 = crossing_time(times, depth_nm, t_off_ms, times[-1], final_state + 0.1 * (on_state - final_state), False)
    crossings = (rise_10, rise_90, decay_90, decay_10)
    if not all(np.isfinite(crossings)):
        raise ValueError("response does not cross every 10%/90% threshold; extend the run or inspect non-monotonic data")

    output = context.root / "LENS_ANALYSIS"
    output.mkdir(parents=True, exist_ok=True)
    response_csv = output / "response.csv"
    with response_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["t_ms", "dOPD_nm", "dn_depth", "dn_center", "RMSE_dn", "f_mm"])
        writer.writerows(rows)

    rise_time = rise_90 - rise_10
    decay_time = decay_10 - decay_90
    summary_lines = [
        f"response project: {project_name}",
        f"switch times: on={t_on_ms:.3f} ms, off={t_off_ms:.3f} ms",
        f"on-state dOPD: {on_state:.1f} nm (Δn depth {on_state * 1e-9 / context.gap_m:.4f})",
        f"rise 10%={rise_10:.1f} ms, 90%={rise_90:.1f} ms -> t_on={rise_time:.1f} ms",
        f"decay 90%={decay_90:.1f} ms, 10%={decay_10:.1f} ms -> t_off={decay_time:.1f} ms",
        f"final dOPD at {times[-1]:.1f} ms: {final_state:.1f} nm",
    ]
    (output / "response_summary.txt").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print("\n".join(summary_lines))

    if make_plot:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as pyplot
        except ImportError:
            print("warning: Matplotlib is unavailable; response CSV and summary were still written", file=sys.stderr)
        else:
            figure, axis = pyplot.subplots(figsize=(7, 4))
            axis.plot(times, values[:, 2], "-")
            axis.axvline(t_on_ms, linestyle=":", color="black")
            axis.axvline(t_off_ms, linestyle=":", color="black")
            axis.set_xlabel("t [ms]")
            axis.set_ylabel("lens depth Δn_eff")
            axis.set_title(f"step response: t_on={rise_time:.0f} ms, t_off={decay_time:.0f} ms")
            figure.tight_layout()
            figure.savefig(output / "response.png", dpi=160)
            pyplot.close(figure)
    return response_csv


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", nargs="?", default=".", help="TechWiz project directory")
    parser.add_argument("--project", help="response project/result prefix")
    parser.add_argument("--parameters", help="parameters JSON path")
    parser.add_argument("--t-on-ms", type=float, help="switch-on time in milliseconds")
    parser.add_argument("--t-off-ms", type=float, help="switch-off time in milliseconds")
    parser.add_argument("--no-plot", action="store_true", help="skip optional response PNG")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        context = lens.load_context(args.project_dir, args.parameters)
        project_name = response_project_name(context, args.project)
        if args.t_on_ms is None or args.t_off_ms is None:
            inferred_on, inferred_off = infer_switch_times(context.parameters.get("signal"))
            t_on_ms = args.t_on_ms if args.t_on_ms is not None else inferred_on
            t_off_ms = args.t_off_ms if args.t_off_ms is not None else inferred_off
        else:
            t_on_ms, t_off_ms = args.t_on_ms, args.t_off_ms
        analyze(context, project_name, t_on_ms, t_off_ms, make_plot=not args.no_plot)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
