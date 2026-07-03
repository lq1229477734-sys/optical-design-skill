# -*- coding: utf-8 -*-
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


try:
    folder_path = Path(__file__).resolve().parent
except NameError:
    folder_path = Path.cwd()

col_index = 31
custom_max = 513
left_min_um = -float("inf")
left_max_um = float("inf")
right_min_um = -float("inf")
right_max_um = float("inf")
save_fig = True
show_fig = False
pause_time = 0.8

if show_fig:
    plt.ion()

angles = np.array([
    -88.5246, -85.5738, -82.623, -79.6721, -76.7213, -73.7705, -70.8197,
    -67.8689, -64.918, -61.9672, -59.0164, -56.0656, -53.1148, -50.1639,
    -47.2131, -44.2623, -41.3115, -38.3607, -35.4098, -32.459, -29.5082,
    -26.5574, -23.6066, -20.6557, -17.7049, -14.7541, -11.8033, -8.85246,
    -5.90164, -2.95082, -1.86517E-14, 2.95082, 5.90164, 8.85246, 11.8033,
    14.7541, 17.7049, 20.6557, 23.6066, 26.5574, 29.5082, 32.459, 35.4098,
    38.3607, 41.3115, 44.2623, 47.2131, 50.1639, 53.1148, 56.0656, 59.0164,
    61.9672, 64.918, 67.8689, 70.8197, 73.7705, 76.7213, 79.6721, 82.623,
    85.5738, 88.5246
], dtype=float)


def show_or_close_current_fig(fig=None):
    if show_fig:
        plt.show(block=False)
        plt.pause(pause_time)
    else:
        plt.close(fig if fig is not None else plt.gcf())


def format_um(x):
    return f"{int(x)}um" if abs(x - int(x)) < 1e-9 else f"{x:g}um"


def natural_key(path):
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r"(\d+)", path.stem)
    ]


def parse_left_right_filename(path):
    name = path.stem.strip()
    pattern = r"^\s*(\d+(?:\.\d+)?)\s*(?:um)?\s*-\s*(\d+(?:\.\d+)?)\s*(?:um)?\s*$"
    match = re.search(pattern, name, re.IGNORECASE)
    if match is None:
        return None, None
    return float(match.group(1)), float(match.group(2))


def read_lighttools_txt(txt_file):
    with open(txt_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    matrix = []
    for line in lines:
        line = line.strip()
        if line == "" or line.startswith("#"):
            continue
        parts = line.replace(",", " ").split()
        try:
            matrix.append([float(x) for x in parts])
        except ValueError:
            continue

    if not matrix:
        raise ValueError(f"{txt_file.name}: no numeric data found")

    min_len = min(len(row) for row in matrix)
    return np.array([row[:min_len] for row in matrix], dtype=float)


def extract_luminance_curve(txt_file):
    data = read_lighttools_txt(txt_file)
    print(f"\nProcessing: {txt_file.name}")
    print("raw matrix shape:", data.shape)

    data_t = data.T
    print("transposed matrix shape:", data_t.shape)

    if data_t.shape[1] < col_index:
        raise ValueError(
            f"{txt_file.name}: transposed matrix has only {data_t.shape[1]} columns; "
            f"cannot read col_index={col_index}"
        )

    y = data_t[:, col_index - 1]
    if len(y) != len(angles):
        raise ValueError(
            f"{txt_file.name}: curve length {len(y)} does not match angle count {len(angles)}"
        )
    return y


def get_lum_0_and_45(y):
    idx_0 = np.argmin(np.abs(angles - 0))
    lum_0 = y[idx_0]
    lum_45_interp = np.interp(45, angles, y)
    idx_45_nearest = np.argmin(np.abs(angles - 45))

    ratio_45_over_0 = lum_45_interp / lum_0 if lum_0 != 0 else np.nan
    ratio_0_over_custom = lum_0 / custom_max if lum_0 != 0 else np.nan
    optical_loss = 1 - ratio_0_over_custom

    return {
        "angle_0_used_deg": angles[idx_0],
        "luminance_0deg": lum_0,
        "angle_45_nearest_deg": angles[idx_45_nearest],
        "luminance_45deg_nearest": y[idx_45_nearest],
        "luminance_45deg_interp": lum_45_interp,
        "ratio_45_over_0": ratio_45_over_0,
        "ratio_45_over_0_percent": ratio_45_over_0 * 100,
        "custom_max": custom_max,
        "ratio_0_over_custom": ratio_0_over_custom,
        "ratio_0_over_custom_percent": ratio_0_over_custom * 100,
        "optical_loss": optical_loss,
        "optical_loss_percent": optical_loss * 100,
    }


def load_all_files():
    txt_files = sorted(folder_path.glob("*.txt"), key=natural_key)
    if not txt_files:
        raise RuntimeError("No txt files found in the current folder")

    output_dir = folder_path / "processed_results_fixed"
    output_dir.mkdir(exist_ok=True)

    all_curves = {}
    all_summary = []

    print("Reading folder:")
    print(folder_path)
    print("\nCandidate txt files:")
    for txt_file in txt_files:
        print(txt_file.name)

    for txt_file in txt_files:
        left_um, right_um = parse_left_right_filename(txt_file)
        if left_um is None or right_um is None:
            print(f"\nSkip filename not matching left-right pattern: {txt_file.name}")
            continue
        if not (left_min_um <= left_um <= left_max_um):
            print(f"\nSkip LeftSurface X Width outside range: {txt_file.name}")
            continue
        if not (right_min_um <= right_um <= right_max_um):
            print(f"\nSkip RightSurface X Width outside range: {txt_file.name}")
            continue

        try:
            y = extract_luminance_curve(txt_file)
            all_curves[(left_um, right_um)] = {
                "left_xwidth_um": left_um,
                "right_xwidth_um": right_um,
                "file_name": txt_file.name,
                "y": y,
            }
            info = get_lum_0_and_45(y)
            all_summary.append({
                "file_name": txt_file.name,
                "left_xwidth_um": left_um,
                "right_xwidth_um": right_um,
                **info,
            })

            curve_csv = output_dir / f"{txt_file.stem}_curve_col{col_index}.csv"
            pd.DataFrame({"Angle_deg": angles, "Luminance_Nit": y}).to_csv(
                curve_csv, index=False, encoding="utf-8-sig"
            )

            print(f"Done: {txt_file.name}")
            print(f"0 deg luminance = {info['luminance_0deg']:.6f}")
            print(f"45 deg interpolated luminance = {info['luminance_45deg_interp']:.6f}")
            print(f"45/0 = {info['ratio_45_over_0_percent']:.6f}%")
            print(f"0/{custom_max} = {info['ratio_0_over_custom_percent']:.6f}%")
            print(f"optical loss = {info['optical_loss_percent']:.6f}%")
        except Exception as exc:
            print(f"\nFailed: {txt_file.name}")
            print("error:", exc)

    if not all_curves:
        raise RuntimeError("No valid txt files were processed")

    summary_df = pd.DataFrame(all_summary).sort_values(by=["left_xwidth_um", "right_xwidth_um"])
    summary_csv = output_dir / "all_files_summary.csv"
    summary_df.to_csv(summary_csv, index=False, encoding="utf-8-sig")
    print("\nSummary saved:")
    print(summary_csv)
    return all_curves, summary_df, output_dir


def plot_one_left_subplots(all_curves, output_dir, left_target):
    right_values = sorted(set(key[1] for key in all_curves))
    n = len(right_values)
    subplot_cols = min(4, n)
    subplot_rows = math.ceil(n / subplot_cols)
    fig, axes = plt.subplots(
        subplot_rows,
        subplot_cols,
        figsize=(4.0 * subplot_cols, 3.2 * subplot_rows),
        sharex=True,
        sharey=True,
    )
    axes = np.array([axes]).flatten() if n == 1 else np.array(axes).flatten()

    for i, ax in enumerate(axes):
        if i >= n:
            ax.axis("off")
            continue
        right = right_values[i]
        key = (left_target, right)
        if key in all_curves:
            ax.plot(
                angles,
                all_curves[key]["y"],
                linewidth=1.5,
                marker="o",
                markersize=2.5,
                label=f"{format_um(left_target)}-{format_um(right)}",
            )
            ax.legend(fontsize=7)
        else:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)

        ax.set_title(f"Right X Width = {format_um(right)}", fontsize=10)
        ax.set_xlabel("Angle (deg)")
        ax.set_ylabel("Luminance")
        ax.grid(True, alpha=0.3)

    fig.suptitle(
        f"Angular luminance curves, Left X Width = {format_um(left_target)}",
        fontsize=14,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.94])

    if save_fig:
        png = output_dir / f"left_{format_um(left_target)}_subplots.png"
        pdf = output_dir / f"left_{format_um(left_target)}_subplots.pdf"
        plt.savefig(png, dpi=300)
        plt.savefig(pdf)
        print(f"\nSubplot saved for left {format_um(left_target)}:")
        print(png)
        print(pdf)
    show_or_close_current_fig(fig)


def plot_all_left_subplots(all_curves, output_dir):
    for left_um in sorted(set(key[0] for key in all_curves)):
        plot_one_left_subplots(all_curves, output_dir, left_um)


def plot_metric_lines(summary_df, output_dir, metric_col, ylabel, title, out_name):
    fig = plt.figure(figsize=(7.8, 5.0))
    for left_um in sorted(summary_df["left_xwidth_um"].unique()):
        df = summary_df[summary_df["left_xwidth_um"] == left_um].sort_values(by="right_xwidth_um")
        plt.plot(
            df["right_xwidth_um"],
            df[metric_col],
            marker="o",
            linewidth=1.8,
            markersize=5,
            label=format_um(left_um),
        )
    plt.xlabel("RightSurface X Width (um)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend(title="LeftSurface X Width")
    plt.tight_layout()

    if save_fig:
        png = output_dir / f"{out_name}.png"
        pdf = output_dir / f"{out_name}.pdf"
        plt.savefig(png, dpi=300)
        plt.savefig(pdf)
        print(f"\nMetric plot saved: {out_name}")
        print(png)
        print(pdf)
    show_or_close_current_fig(fig)


def plot_heatmap(summary_df, output_dir, metric_col, title, out_name):
    pivot = summary_df.pivot(index="left_xwidth_um", columns="right_xwidth_um", values=metric_col)
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    im = ax.imshow(pivot.values, aspect="auto", origin="lower", cmap="viridis")
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels([format_um(x) for x in pivot.columns])
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels([format_um(x) for x in pivot.index])
    ax.set_xlabel("RightSurface X Width")
    ax.set_ylabel("LeftSurface X Width")
    ax.set_title(title)
    cbar = fig.colorbar(im, ax=ax)
    cbar.ax.set_ylabel(metric_col)

    for row in range(pivot.shape[0]):
        for col in range(pivot.shape[1]):
            value = pivot.values[row, col]
            if np.isfinite(value):
                ax.text(col, row, f"{value:.2f}", ha="center", va="center", color="white", fontsize=8)

    fig.tight_layout()
    if save_fig:
        png = output_dir / f"{out_name}.png"
        pdf = output_dir / f"{out_name}.pdf"
        plt.savefig(png, dpi=300)
        plt.savefig(pdf)
        print(f"\nHeatmap saved: {out_name}")
        print(png)
        print(pdf)
    show_or_close_current_fig(fig)
    return pivot


def save_pivot_tables(summary_df, output_dir):
    ratio_45_pivot = summary_df.pivot(
        index="left_xwidth_um",
        columns="right_xwidth_um",
        values="ratio_45_over_0_percent",
    )
    ratio_0_pivot = summary_df.pivot(
        index="left_xwidth_um",
        columns="right_xwidth_um",
        values="ratio_0_over_custom_percent",
    )
    loss_pivot = summary_df.pivot(
        index="left_xwidth_um",
        columns="right_xwidth_um",
        values="optical_loss_percent",
    )

    ratio_45_pivot.to_csv(output_dir / "pivot_ratio_45_over_0_percent.csv", encoding="utf-8-sig")
    ratio_0_pivot.to_csv(output_dir / f"pivot_ratio_0_over_{custom_max}_percent.csv", encoding="utf-8-sig")
    loss_pivot.to_csv(
        output_dir / f"pivot_optical_loss_1_minus_0deg_over_{custom_max}_percent.csv",
        encoding="utf-8-sig",
    )
    print("\nPivot tables saved.")


if __name__ == "__main__":
    all_curves, summary_df, output_dir = load_all_files()
    print("\nRecognized LeftSurface X Width values:")
    print([format_um(x) for x in sorted(summary_df["left_xwidth_um"].unique())])
    print("\nRecognized RightSurface X Width values:")
    print([format_um(x) for x in sorted(summary_df["right_xwidth_um"].unique())])

    plot_all_left_subplots(all_curves, output_dir)
    plot_metric_lines(
        summary_df,
        output_dir,
        "ratio_45_over_0_percent",
        "45 deg / 0 deg (%)",
        "45 deg / 0 deg ratio vs RightSurface X Width",
        "ratio_45_over_0_vs_right_xwidth_left_curves",
    )
    plot_metric_lines(
        summary_df,
        output_dir,
        "optical_loss_percent",
        "Optical Loss (%)",
        f"Optical Loss = 1 - 0 deg luminance / {custom_max}",
        f"optical_loss_1_minus_0deg_over_{custom_max}_vs_right_xwidth",
    )
    plot_heatmap(
        summary_df,
        output_dir,
        "ratio_45_over_0_percent",
        "45 deg / 0 deg ratio (%)",
        "heatmap_ratio_45_over_0_percent",
    )
    plot_heatmap(
        summary_df,
        output_dir,
        "optical_loss_percent",
        "Optical loss (%)",
        "heatmap_optical_loss_percent",
    )
    save_pivot_tables(summary_df, output_dir)
    print("\nAll processing finished.")
    print("Results folder:")
    print(output_dir)

    if show_fig:
        plt.ioff()
        plt.show()
