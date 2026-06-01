#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Post-process LightTools Angular_Luminance_Mesh txt exports.

Expected file names look like:
    50um-90um.txt
    70um-130um.txt
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ANGLES = np.array(
    [
        -88.5246,
        -85.5738,
        -82.623,
        -79.6721,
        -76.7213,
        -73.7705,
        -70.8197,
        -67.8689,
        -64.918,
        -61.9672,
        -59.0164,
        -56.0656,
        -53.1148,
        -50.1639,
        -47.2131,
        -44.2623,
        -41.3115,
        -38.3607,
        -35.4098,
        -32.459,
        -29.5082,
        -26.5574,
        -23.6066,
        -20.6557,
        -17.7049,
        -14.7541,
        -11.8033,
        -8.85246,
        -5.90164,
        -2.95082,
        -1.86517e-14,
        2.95082,
        5.90164,
        8.85246,
        11.8033,
        14.7541,
        17.7049,
        20.6557,
        23.6066,
        26.5574,
        29.5082,
        32.459,
        35.4098,
        38.3607,
        41.3115,
        44.2623,
        47.2131,
        50.1639,
        53.1148,
        56.0656,
        59.0164,
        61.9672,
        64.918,
        67.8689,
        70.8197,
        73.7705,
        76.7213,
        79.6721,
        82.623,
        85.5738,
        88.5246,
    ],
    dtype=float,
)


def parse_um_pair(path: Path) -> tuple[float | None, float | None]:
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*um\s*-\s*(\d+(?:\.\d+)?)\s*um",
        path.stem,
        re.IGNORECASE,
    )
    if match is None:
        return None, None
    return float(match.group(1)), float(match.group(2))


def natural_key(path: Path) -> list[object]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.stem)]


def read_mesh_txt(path: Path) -> np.ndarray:
    rows: list[list[float]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                rows.append([float(item) for item in line.replace(",", " ").split()])
            except ValueError:
                continue

    if not rows:
        raise ValueError(f"{path.name}: no numeric mesh rows found")

    min_len = min(len(row) for row in rows)
    return np.array([row[:min_len] for row in rows], dtype=float)


def extract_curve(path: Path, col_index: int) -> np.ndarray:
    mesh = read_mesh_txt(path)
    curve = mesh.T[:, col_index - 1]
    if len(curve) != len(ANGLES):
        raise ValueError(
            f"{path.name}: extracted {len(curve)} points, expected {len(ANGLES)}. "
            f"Check col_index={col_index} and txt mesh shape={mesh.shape}."
        )
    return curve


def summarize_curve(curve: np.ndarray, custom_max: float) -> dict[str, float]:
    idx0 = int(np.argmin(np.abs(ANGLES)))
    lum0 = float(curve[idx0])
    lum45 = float(np.interp(45, ANGLES, curve))
    ratio = np.nan if lum0 == 0 else lum45 / lum0
    ratio0 = np.nan if custom_max == 0 else lum0 / custom_max
    return {
        "angle_0_used_deg": float(ANGLES[idx0]),
        "luminance_0deg": lum0,
        "luminance_45deg_interp": lum45,
        "ratio_45_over_0": ratio,
        "ratio_45_over_0_percent": ratio * 100,
        "custom_max": custom_max,
        "ratio_0_over_custom": ratio0,
        "ratio_0_over_custom_percent": ratio0 * 100,
        "optical_loss": 1 - ratio0,
        "optical_loss_percent": (1 - ratio0) * 100,
    }


def fmt_um(value: float) -> str:
    return f"{int(value)}um" if abs(value - int(value)) < 1e-9 else f"{value:g}um"


def plot_metric(df: pd.DataFrame, metric: str, ylabel: str, out_path: Path) -> None:
    plt.figure(figsize=(7, 4.5), dpi=150)
    for first_um, group in sorted(df.groupby("first_um")):
        group = group.sort_values("second_um")
        plt.plot(group["second_um"], group[metric], marker="o", label=f"{fmt_um(first_um)}")
    plt.xlabel("second length (um)")
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.legend(title="first length")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True, type=Path)
    parser.add_argument("--front-min", type=float, default=-np.inf)
    parser.add_argument("--front-max", type=float, default=np.inf)
    parser.add_argument("--back-min", type=float, default=-np.inf)
    parser.add_argument("--back-max", type=float, default=np.inf)
    parser.add_argument("--col-index", type=int, default=31)
    parser.add_argument("--custom-max", type=float, default=513.0)
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()

    folder = args.folder.resolve()
    out_dir = args.out_dir or (folder / "processed_results_fixed")
    out_dir.mkdir(parents=True, exist_ok=True)

    summaries: list[dict[str, float | str]] = []
    txt_files = sorted(folder.glob("*.txt"), key=natural_key)
    if not txt_files:
        raise RuntimeError(f"No txt files found in {folder}")

    for txt_file in txt_files:
        first_um, second_um = parse_um_pair(txt_file)
        if first_um is None or second_um is None:
            continue
        if not (args.front_min <= first_um <= args.front_max and args.back_min <= second_um <= args.back_max):
            continue

        curve = extract_curve(txt_file, args.col_index)
        curve_df = pd.DataFrame({"angle_deg": ANGLES, "luminance": curve})
        curve_df.to_csv(out_dir / f"{txt_file.stem}_curve_col{args.col_index}.csv", index=False)

        summary = summarize_curve(curve, args.custom_max)
        summary.update({"file": txt_file.name, "first_um": first_um, "second_um": second_um})
        summaries.append(summary)

    if not summaries:
        raise RuntimeError("No matching txt files were processed. Check filename pattern and ranges.")

    df = pd.DataFrame(summaries).sort_values(["first_um", "second_um"])
    df.to_csv(out_dir / "all_files_summary.csv", index=False)

    for metric in ["luminance_0deg", "ratio_45_over_0_percent", "optical_loss_percent"]:
        pivot = df.pivot(index="first_um", columns="second_um", values=metric)
        pivot.to_csv(out_dir / f"pivot_{metric}.csv")

    plot_metric(df, "ratio_45_over_0_percent", "45 deg / 0 deg (%)", out_dir / "ratio_45_over_0_vs_second_um_first_curves.png")
    plot_metric(df, "optical_loss_percent", "optical loss (%)", out_dir / "optical_loss_vs_second_um_first_curves.png")

    print(f"Processed {len(df)} files")
    print(f"Saved results to: {out_dir}")


if __name__ == "__main__":
    main()
