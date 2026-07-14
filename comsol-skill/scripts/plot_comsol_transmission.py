from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

C_UM_THz = 299.792458


def read_table(path: Path) -> tuple[np.ndarray, np.ndarray]:
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip() or line.lstrip().startswith("%"):
            continue
        freq, value = line.split()[:2]
        rows.append((float(freq), float(value)))
    if not rows:
        raise ValueError(f"No numeric COMSOL rows in {path}")
    data = np.asarray(rows, dtype=float)
    return data[:, 0], data[:, 1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lcp", type=Path, required=True)
    parser.add_argument("--rcp", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Output stem without extension")
    parser.add_argument("--title", default=r"COMSOL transmission of a twisted $\alpha$-MoO$_3$ bilayer")
    args = parser.parse_args()

    freq, tl = read_table(args.lcp)
    freq_r, tr = read_table(args.rcp)
    if not np.allclose(freq, freq_r):
        raise ValueError("LCP and RCP frequency grids do not match")
    wavelength = C_UM_THz / freq
    order = np.argsort(wavelength)
    wavelength, freq, tl, tr = wavelength[order], freq[order], tl[order], tr[order]
    delta = tl - tr
    cd = np.abs(delta)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.with_suffix(".csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["wavelength_um", "frequency_THz", "T_LCP", "T_RCP", "delta_T", "CD_abs"])
        writer.writerows(zip(wavelength, freq, tl, tr, delta, cd))

    mpl.rcParams.update({
        "font.family": "sans-serif", "font.size": 8, "axes.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False, "svg.fonttype": "none", "pdf.fonttype": 42,
    })
    fig, (a, b) = plt.subplots(2, 1, figsize=(7.1, 5.2), sharex=True,
                               gridspec_kw={"height_ratios": [2.05, 1], "hspace": 0.08})
    mark = max(1, len(wavelength) // 20)
    a.plot(wavelength, tl, color="#C63D3D", lw=1.8, marker="o", ms=3, markevery=mark, label="LCP")
    a.plot(wavelength, tr, color="#2468A2", lw=1.8, marker="s", ms=2.8, markevery=mark, label="RCP")
    a.set_ylabel("Transmittance"); a.set_ylim(0, max(1.03, float(max(tl.max(), tr.max())) * 1.05)); a.legend(ncol=2)
    b.fill_between(wavelength, 0, cd, color="#2E8B57", alpha=0.16, linewidth=0)
    b.plot(wavelength, cd, color="#2E8B57", lw=1.9, marker="o", ms=3, markevery=mark,
           label=r"CD = $|T_{LCP}-T_{RCP}|$")
    b.set_ylabel("CD"); b.set_xlabel(r"Wavelength ($\mu$m)"); b.legend()
    for ax in (a, b): ax.grid(axis="y", color="#D9D9D9", lw=0.55, alpha=0.7)
    fig.suptitle(args.title, fontsize=10)
    fig.subplots_adjust(left=0.11, right=0.98, bottom=0.11, top=0.92)
    fig.savefig(args.output.with_suffix(".png"), dpi=300, facecolor="white")
    fig.savefig(args.output.with_suffix(".svg"), facecolor="white")
    fig.savefig(args.output.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)
    print(f"rows={len(wavelength)} T={min(tl.min(), tr.min()):.6g}..{max(tl.max(), tr.max()):.6g} max_CD={cd.max():.6g}")


if __name__ == "__main__":
    main()
