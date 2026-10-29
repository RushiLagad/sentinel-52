#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-26. Review it
# before relying on it.
# -----------------------------------------------------------------------------
"""Figure: what FSIS sampling finds in chicken against what puts people in hospital.

Both quantities are shown as a share of the four serotypes plotted, because the
two underlying denominators are different things (serotyped isolates in FSIS
sampling; outbreak-associated hospitalizations in NORS) and cannot share a raw axis. Normalising to the plotted four makes the ORDERING comparable, which is
the claim. It does not make the levels comparable, and the figure says so.

Usage:
  python scripts/10b_figure_prevalence_vs_burden.py --out outputs
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BLUE, ORANGE, INK, MUTED, SURFACE, GRID = "#2a78d6", "#eb6834", "#1c1c1a", "#8a8a85", "#fcfcfb", "#e6e6e2"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()

    D = pd.read_csv(a.out / "t17_chicken_prevalence_vs_burden.csv")
    D = D.rename(columns={"fsis_share_of_serotyped_chicken_isolates_pct_latest_fy": "fsis_pct",
                          "nors_chicken_hospitalizations": "hosp"})
    D["prev_share"] = 100 * D["fsis_pct"] / D["fsis_pct"].sum()
    D["burden_share"] = 100 * D["hosp"] / D["hosp"].sum()
    D = D.sort_values("prev_share", ascending=False).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(7.6, 4.6), dpi=200)
    fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)

    y = range(len(D)); h = 0.34
    ax.barh([v + h / 2 + 0.01 for v in y], D["prev_share"], height=h, color=BLUE,
            label="Share of serotyped FSIS chicken isolates, FY2026")
    ax.barh([v - h / 2 - 0.01 for v in y], D["burden_share"], height=h, color=ORANGE,
            label="Share of outbreak hospitalizations, chicken, 2014-2023")

    for i, r in D.iterrows():
        ax.text(r["prev_share"] + 1.2, i + h / 2 + 0.01, f"{r['prev_share']:.0f}%",
                va="center", fontsize=8.5, color=INK)
        lbl = f"{r['burden_share']:.0f}%" + ("  (0 of 237)" if r["hosp"] == 0 else f"  ({int(r['hosp'])})")
        ax.text(r["burden_share"] + 1.2, i - h / 2 - 0.01, lbl, va="center", fontsize=8.5, color=INK)

    ax.set_yticks(list(y)); ax.set_yticklabels(D["serotype"], fontsize=10, color=INK)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of the four serotypes shown (%)", color=INK, fontsize=9.5)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(MUTED); ax.spines["bottom"].set_linewidth(0.8)
    ax.tick_params(colors=MUTED, labelsize=8.5)
    ax.tick_params(axis="y", length=0)
    ax.grid(True, axis="x", lw=0.6, color=GRID, zorder=0)
    ax.set_axisbelow(True)
    leg = ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    for t in leg.get_texts():
        t.set_color(INK)

    fig.subplots_adjust(left=0.135, right=0.975, top=0.80, bottom=0.145)
    fig.text(0.02, 0.955, "What sampling finds is not what sends people to hospital",
             color=INK, fontsize=13, va="top")
    fig.text(0.02, 0.895,
             "Kentucky is a fifth of serotyped chicken isolates and zero hospitalizations in ten years.",
             color=MUTED, fontsize=8.5, va="top")
    fig.text(0.02, 0.862,
             "Shares are of these four only; the two measures have different denominators, so compare "
             "the ordering, not the levels.",
             color=MUTED, fontsize=8.5, va="top")

    (a.out / "figures").mkdir(exist_ok=True)
    fig.savefig(a.out / "figures" / "fig5_prevalence_vs_burden.png", facecolor=SURFACE)
    plt.close(fig)
    print(D[["serotype", "fsis_pct", "prev_share", "hosp", "burden_share"]].round(1).to_string(index=False))
    print(f"\nwrote {a.out/'figures'/'fig5_prevalence_vs_burden.png'}")


if __name__ == "__main__":
    main()
