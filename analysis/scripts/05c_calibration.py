#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-26. Review it
# before relying on it.
# -----------------------------------------------------------------------------
"""Reliability of the risk scores, for the scorer the tool actually displays.

The brief requires discrimination AND calibration. `05_early_warning_baseline.py`
already reports Brier per scorer and a decile reliability table for gradient
boosting. This script adds the same for the **binomial projection**, which is the
default scorer in the decision layer and therefore the one that has to be
calibrated, and writes a reliability figure.

Why this matters operationally: a food bank holding a lot on a "30 percent" score
needs that 30 percent to mean something. A score that ranks well but is
systematically over-confident will cause avoidable food loss at every threshold.

Reads the test-period scores emitted by 05 (strictly out of sample: trained on
month-ends through mid-2022, tested on 2024-2025).

Usage:
  python scripts/05c_calibration.py --out outputs --horizon 6
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SCORERS = {"projection": "Binomial projection", "gb": "Gradient boosting"}
BLUE, ORANGE, INK, MUTED, SURFACE = "#2a78d6", "#eb6834", "#1c1c1a", "#8a8a85", "#fcfcfb"


def reliability(y: np.ndarray, s: np.ndarray, bins: int = 10) -> pd.DataFrame:
    """Equal-count bins over the score, with the observed rate in each."""
    df = pd.DataFrame({"y": y, "s": s})
    # rank first so ties (the projection has many exact zeros) spread across bins
    df["bin"] = pd.qcut(df["s"].rank(method="first"), bins, labels=False)
    g = df.groupby("bin").agg(mean_pred=("s", "mean"), observed=("y", "mean"), n=("y", "size"))
    g["gap"] = g["observed"] - g["mean_pred"]
    return g.reset_index()


def ece(tab: pd.DataFrame) -> float:
    """Expected calibration error: average |observed - predicted|, weighted by bin size."""
    w = tab["n"] / tab["n"].sum()
    return float((w * (tab["observed"] - tab["mean_pred"]).abs()).sum())


def brier(y: np.ndarray, s: np.ndarray) -> float:
    return float(np.mean((np.clip(s, 0, 1) - y) ** 2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--horizon", type=int, default=6)
    ap.add_argument("--bins", type=int, default=10)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    src = a.out / f"early_warning_test_scores_h{a.horizon}.parquet"
    if not src.exists():
        raise SystemExit(f"{src} not found. Run 05_early_warning_baseline.py first.")
    T = pd.read_parquet(src)
    base = float(T["y"].mean())

    res: dict = {
        "horizon_months": a.horizon,
        "test_rows": int(len(T)),
        "test_base_rate": round(base, 4),
        "test_window_ends": [str(T["window_end"].min().date()), str(T["window_end"].max().date())],
        "bins": a.bins,
        "scorers": {},
    }
    tables = []
    for col, label in SCORERS.items():
        tab = reliability(T["y"].to_numpy(), T[col].to_numpy(), a.bins)
        res["scorers"][col] = {
            "label": label,
            "brier": round(brier(T["y"].to_numpy(), T[col].to_numpy()), 4),
            "ece": round(ece(tab), 4),
            # calibration-in-the-large: does the average prediction match the base rate at all?
            "mean_prediction": round(float(T[col].mean()), 4),
            "base_rate": round(base, 4),
            "mean_pred_minus_base": round(float(T[col].mean()) - base, 4),
            "top_bin_predicted": round(float(tab["mean_pred"].iloc[-1]), 4),
            "top_bin_observed": round(float(tab["observed"].iloc[-1]), 4),
            "reliability": tab.round(4).to_dict(orient="records"),
        }
        tables.append(tab.assign(scorer=col))

    pd.concat(tables).to_csv(a.out / f"t18_reliability_h{a.horizon}.csv", index=False)
    (a.out / f"calibration_h{a.horizon}.json").write_text(json.dumps(res, indent=1))

    # ---- figure
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.0, 5.8), dpi=200)
    fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)
    ax.plot([0, 1], [0, 1], lw=1, color=MUTED, ls=(0, (4, 3)), zorder=1, label="Perfect calibration")
    for (col, label), color in zip(SCORERS.items(), (BLUE, ORANGE)):
        tab = pd.DataFrame(res["scorers"][col]["reliability"])
        ax.plot(tab["mean_pred"], tab["observed"], lw=2, marker="o", ms=6, color=color,
                label=f"{label}  (Brier {res['scorers'][col]['brier']}, ECE {res['scorers'][col]['ece']})",
                zorder=3, markeredgecolor=SURFACE, markeredgewidth=1.4)
    ax.set_xscale("log"); ax.set_yscale("log")
    lo = 3e-4
    ax.set_xlim(lo, 1); ax.set_ylim(lo, 1)
    ax.set_xlabel("Predicted probability of entering Category 3", color=INK, fontsize=9.5)
    ax.set_ylabel("Observed rate", color=INK, fontsize=9.5)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED); ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=MUTED, labelsize=8.5)
    ax.grid(True, which="major", lw=0.6, color="#e6e6e2", zorder=0)
    leg = ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    for t in leg.get_texts():
        t.set_color(INK)

    fig.subplots_adjust(left=0.11, right=0.97, top=0.805, bottom=0.105)
    fig.text(0.02, 0.955, "The projection under-states low risk and over-states high risk",
             color=INK, fontsize=12.5, va="top", ha="left")
    fig.text(0.02, 0.900,
             f"Decile bins, held out {res['test_window_ends'][0]} to {res['test_window_ends'][1]}, "
             f"base rate {base:.1%}.",
             color=MUTED, fontsize=8.5, va="top", ha="left")
    fig.text(0.02, 0.868, "Points above the dashed line fail more often than the score predicts.",
             color=MUTED, fontsize=8.5, va="top", ha="left")
    (a.out / "figures").mkdir(exist_ok=True)
    fig.savefig(a.out / "figures" / f"fig4_reliability_h{a.horizon}.png", facecolor=SURFACE)
    plt.close(fig)

    for col in SCORERS:
        s = res["scorers"][col]
        print(f"{s['label']:<22} Brier {s['brier']}  ECE {s['ece']}  "
              f"top decile: predicted {s['top_bin_predicted']} vs observed {s['top_bin_observed']}")
    print(f"\nwrote {a.out/f'calibration_h{a.horizon}.json'}")


if __name__ == "__main__":
    main()
