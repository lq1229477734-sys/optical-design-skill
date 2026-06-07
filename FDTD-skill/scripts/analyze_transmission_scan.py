#!/usr/bin/env python3
"""Convert a transmission scan text table to CSV and PNG."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="TXT table with phase thickness wavelength transmission columns")
    parser.add_argument("--csv", help="Output CSV path")
    parser.add_argument("--png", help="Output PNG path")
    parser.add_argument("--title", default="Transmission scan")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).resolve()
    csv_path = Path(args.csv).resolve() if args.csv else input_path.with_suffix(".csv")
    png_path = Path(args.png).resolve() if args.png else input_path.with_suffix(".png")

    rows: list[tuple[float, float, float, float, float]] = []
    with input_path.open("r", encoding="utf-8") as handle:
        header = handle.readline().split()
        if len(header) < 4:
            raise ValueError("Expected at least four columns in the header")
        for line in handle:
            if not line.strip():
                continue
            phase, thickness, wavelength, transmission = [float(x) for x in line.split()[:4]]
            rows.append((phase, thickness, wavelength, transmission, abs(transmission)))

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["phase_deg", "thickness_m", "wavelength_nm", "transmission_raw", "transmission_abs"])
        writer.writerows(rows)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    data = np.array(rows)
    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=160)
    for phase in sorted(set(data[:, 0])):
        part = data[data[:, 0] == phase]
        part = part[np.argsort(part[:, 2])]
        ax.plot(part[:, 2], part[:, 4], marker="o", markersize=3, linewidth=1.8, label=f"phase {phase:g} deg")

    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("|Transmission|")
    ax.set_title(args.title)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(png_path)
    plt.close(fig)

    print(f"Wrote {csv_path}")
    print(f"Wrote {png_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
