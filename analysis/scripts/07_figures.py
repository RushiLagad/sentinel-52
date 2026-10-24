#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-09 and run end to
# end on the real FSIS files. Review it before relying on it.
# -----------------------------------------------------------------------------
"""Three summary figures built only from tables the other scripts wrote.

  outputs/figures/fig1_positivity_serotypes_resistance.png
  outputs/figures/fig2_who_fails_and_how_early.png
  outputs/figures/fig3_fsis_indicator_vs_target.png

Every number plotted is also in a CSV or JSON in outputs/ (the table view).
Palette and mark sizes follow a validated colour-blind-safe scheme: blue
#2a78d6, orange #eb6834, aqua #1baf7a on a #fcfcfb surface.

Usage:
  python scripts/07_figures.py --data data/processed --out outputs
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath

SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA, DEEMPH = "#2a78d6", "#eb6834", "#1baf7a", "#b4b2aa"
PX = 72 / 100  # one design pixel in points (figures are laid out at 100 px per inch, saved at 2x)
DPI = 200

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11 * PX, "axes.edgecolor": AXIS, "axes.linewidth": 1 * PX,
                     "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 11 * PX, "ytick.labelsize": 11 * PX,
                     "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE})


def style(ax, grid_axis="y"):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.spines["left"].set_visible(grid_axis == "x"); ax.spines["bottom"].set_visible(grid_axis == "y")
    ax.grid(axis=grid_axis, color=GRID, linewidth=1 * PX, linestyle="-"); ax.set_axisbelow(True)
    ax.tick_params(length=0, pad=5 * PX)


def titles(ax, title, subtitle):
    ax.text(0, 1.35, title, transform=ax.transAxes, fontsize=14 * PX, fontweight="bold", color=INK, va="bottom", ha="left")
    ax.text(0, 1.325, subtitle, transform=ax.transAxes, fontsize=11 * PX, color=INK2, va="top", ha="left", linespacing=1.3)


def three_axes(fig, lefts=(0.045, 0.385, 0.765), widths=(0.265, 0.265, 0.205)):
    """Three panels with hand-set positions so long row labels on the third panel have room."""
    return [fig.add_axes([l, 0.15, w, 0.55]) for l, w in zip(lefts, widths)]


def line(ax, x, y, color, lw=2.0, end_marker=True, zorder=3):
    ax.plot(x, y, color=color, linewidth=lw * PX, solid_capstyle="round", solid_joinstyle="round", zorder=zorder)
    if end_marker:
        ax.plot([x[-1]], [y[-1]], marker="o", markersize=10 * PX, markerfacecolor=color, markeredgecolor=SURFACE, markeredgewidth=2 * PX, zorder=zorder + 1, linestyle="none")


def legend(ax, items, y=1.035):
    handles = [Line2D([0], [0], color=c, linewidth=2 * PX, marker=m, markersize=7 * PX, markerfacecolor=c, markeredgecolor=c) for _, c, m in items]
    ax.legend(handles, [n for n, _, _ in items], loc="lower left", bbox_to_anchor=(-0.01, y), ncol=len(items), frameon=False, fontsize=10.5 * PX,
              labelcolor=INK2, handlelength=1.6, columnspacing=1.4, handletextpad=0.5, borderaxespad=0)


def rounded_bars(fig, ax, positions, values, color, horizontal=False, thickness_px=22, radius_px=4):
    """Bars with a rounded data end and a square baseline, sized in pixels. Call after limits are final."""
    fig.canvas.draw()
    s = fig.dpi / 100
    t, r = thickness_px * s, radius_px * s
    for p, v in zip(positions, values):
        if horizontal:
            x0, yc = ax.transData.transform((0, p)); x1, _ = ax.transData.transform((v, p))
            L = max(x1 - x0, 0.01); rr = min(r, L)
            verts = [(x0, yc - t / 2), (x1 - rr, yc - t / 2), (x1, yc - t / 2), (x1, yc - t / 2 + rr), (x1, yc + t / 2 - rr), (x1, yc + t / 2), (x1 - rr, yc + t / 2), (x0, yc + t / 2), (x0, yc - t / 2)]
        else:
            xc, y0 = ax.transData.transform((p, 0)); _, y1 = ax.transData.transform((p, v))
            L = max(y1 - y0, 0.01); rr = min(r, L)
            verts = [(xc - t / 2, y0), (xc - t / 2, y1 - rr), (xc - t / 2, y1), (xc - t / 2 + rr, y1), (xc + t / 2 - rr, y1), (xc + t / 2, y1), (xc + t / 2, y1 - rr), (xc + t / 2, y0), (xc - t / 2, y0)]
        codes = [MPath.MOVETO, MPath.LINETO, MPath.CURVE3, MPath.CURVE3, MPath.LINETO, MPath.CURVE3, MPath.CURVE3, MPath.LINETO, MPath.CLOSEPOLY]
        fig.add_artist(PathPatch(MPath(verts, codes), facecolor=color, edgecolor="none", transform=None, zorder=3))


def fig1(out: Path) -> None:
    t1 = pd.read_csv(out / "t1_routine_positivity_by_fy.csv"); t2 = pd.read_csv(out / "t2b_chicken_serotype_share_routine_only.csv").set_index("fy")
    t13 = pd.read_csv(out / "t13_fsis_wgs_resistance_by_serotype.csv")
    fig = plt.figure(figsize=(15.0, 4.6), dpi=DPI); axes = three_axes(fig)

    ax = axes[0]; style(ax)
    piv = t1.pivot(index="fy", columns="product_class", values="pct").loc[2015:]
    yrs = piv.index.to_numpy()
    for cls, col in [("chicken_parts", BLUE), ("chicken_carcass", ORANGE)]:
        line(ax, yrs, piv[cls].to_numpy(), col)
    ax.set_ylim(0, 27); ax.set_xlim(2014.6, 2028.6); ax.set_xticks([2015, 2017, 2019, 2021, 2023, 2025]); ax.set_xticklabels(["FY15", "FY17", "FY19", "FY21", "FY23", "FY25"])
    ax.set_yticks([0, 5, 10, 15, 20, 25]); ax.set_yticklabels(["0", "5", "10", "15", "20", "25%"])
    ax.annotate(f"{piv['chicken_parts'].iloc[-1]:.1f}%", (yrs[-1], piv["chicken_parts"].iloc[-1]), xytext=(9 * PX, 0), textcoords="offset points", va="center", fontsize=11 * PX, color=INK)
    ax.annotate(f"{piv['chicken_carcass'].iloc[-1]:.1f}%", (yrs[-1], piv["chicken_carcass"].iloc[-1]), xytext=(9 * PX, 0), textcoords="offset points", va="center", fontsize=11 * PX, color=INK)
    titles(ax, "Positivity stopped falling after FY2021", "Routine samples positive for Salmonella, by fiscal year")
    legend(ax, [("Chicken parts", BLUE, None), ("Young chicken carcasses", ORANGE, None)], y=1.04)

    ax = axes[1]; style(ax)
    t2 = t2.loc[2015:]; yrs = t2.index.to_numpy()
    for s in ("Enteritidis", "Typhimurium"):
        line(ax, yrs, t2[s].to_numpy(), DEEMPH, lw=2.0, zorder=2)
    line(ax, yrs, t2["Kentucky"].to_numpy(), ORANGE); line(ax, yrs, t2["Infantis"].to_numpy(), BLUE)
    ax.set_ylim(0, 45); ax.set_xlim(2014.6, 2030.2); ax.set_xticks([2015, 2017, 2019, 2021, 2023, 2025]); ax.set_xticklabels(["FY15", "FY17", "FY19", "FY21", "FY23", "FY25"])
    ax.set_yticks([0, 10, 20, 30, 40]); ax.set_yticklabels(["0", "10", "20", "30", "40%"])
    for s in ("Infantis", "Enteritidis", "Kentucky", "Typhimurium"):
        ax.annotate(f"{s} {t2[s].iloc[-1]:.0f}%", (yrs[-1], t2[s].iloc[-1]), xytext=(9 * PX, 0), textcoords="offset points", va="center", fontsize=11 * PX, color=INK)
    titles(ax, "The mix shifted toward Infantis", "Share of serotyped chicken isolates, routine samples")
    legend(ax, [("Infantis", BLUE, None), ("Kentucky", ORANGE, None), ("Other leading serotypes", DEEMPH, None)], y=1.04)

    ax = axes[2]; style(ax, grid_axis="x")
    d = t13[(t13["species"] == "chicken") & t13["serotype_clean"].isin(["Infantis", "Typhimurium", "Kentucky", "Enteritidis", "Schwarzengrund"])].sort_values("mdr3_pct")
    pos = np.arange(len(d)); ax.set_ylim(-0.6, len(d) - 0.4); ax.set_xlim(0, 100)
    ax.set_yticks(pos); ax.set_yticklabels([f"{s}\n{n:,} isolates" for s, n in zip(d["serotype_clean"], d["isolates"])], color=INK2, linespacing=1.25)
    ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xticklabels(["0", "25", "50", "75", "100%"])
    titles(ax, "Infantis is mostly multidrug resistant", "Chicken isolates resistant to 3 or more drug classes,\nFSIS sequence-based calls, FY2024 to FY2026")
    rounded_bars(fig, ax, pos, d["mdr3_pct"].to_numpy(), BLUE, horizontal=True)
    for p, v in zip(pos, d["mdr3_pct"]):
        ax.annotate(f"{v:.0f}%" if v >= 1 else f"{v:.1f}%", (v, p), xytext=(7 * PX, 0), textcoords="offset points", va="center", fontsize=11 * PX, color=INK)
    fig.text(0.045, 0.035, "Source: FSIS establishment-specific raw poultry sampling data (files posted Oct 2, 2026). FY2026 covers Oct 2025 to Jun 2026. Preliminary analysis, routine verification samples only.",
             fontsize=9.5 * PX, color=MUTED, ha="left")
    (out / "figures").mkdir(exist_ok=True); fig.savefig(out / "figures" / "fig1_positivity_serotypes_resistance.png", dpi=DPI); plt.close(fig)


def fig2(data: Path, out: Path) -> None:
    agg = pd.read_parquet(data / "posted_aggregate.parquet"); ew = json.loads((out / "early_warning_summary_h6.json").read_text()); wl = json.loads((out / "watchlist_comparison_h6.json").read_text())
    fig = plt.figure(figsize=(15.0, 4.6), dpi=DPI); axes = three_axes(fig)

    ax = axes[0]; style(ax)
    sz = agg[agg["haccp_size"] != "All"].groupby(["haccp_size", "category"])["establishments"].sum().unstack()
    order = ["Large", "Small", "Very Small"]; n3 = sz.loc[order, "3"].to_numpy(); tot = sz.loc[order].sum(axis=1).to_numpy(); pct = 100 * n3 / tot
    pos = np.arange(3); ax.set_xlim(-0.6, 2.6); ax.set_ylim(0, 32); ax.set_yticks([0, 10, 20, 30]); ax.set_yticklabels(["0", "10", "20", "30%"])
    ax.set_xticks(pos); ax.set_xticklabels([f"{o}\n{a} of {b}" for o, a, b in zip(["Large", "Small", "Very small"], n3, tot)], color=INK2)
    window = agg["window_text"].iloc[0].replace("for Sample Collection Period ", "")
    titles(ax, "Failing is concentrated in smaller plants", f"Rated plant and product pairs in Category 3, by HACCP size,\nFSIS posting for {window.replace(' through ', ' to ')}")
    rounded_bars(fig, ax, pos, pct, BLUE)
    for p, v in zip(pos, pct):
        ax.annotate(f"{v:.1f}%", (p, v), xytext=(0, 6 * PX), textcoords="offset points", ha="center", fontsize=11 * PX, color=INK)

    ax = axes[1]; style(ax)
    lt = wl["lead_time"]["on_list_at_least_k_months_before_pct"]; ks = np.arange(1, 7); med = wl["median_units_per_month"]
    series = [("category_2_flag", f"Category 2 today (about {med['category_2_flag']:.0f} units a month)", BLUE),
              ("projection_same_size", "Projection, same list size", ORANGE),
              ("projection_top10pct", f"Projection, top 10% (about {med['projection_top10pct']:.0f} units)", AQUA)]
    for key, _, col in series:
        line(ax, ks, np.array([lt[key][str(k)] for k in ks]), col)
    ax.set_ylim(0, 100); ax.set_xlim(0.7, 7.25); ax.set_xticks(ks); ax.set_xticklabels(["1", "2", "3", "4", "5", "6"]); ax.set_xlabel("Months before the unit entered Category 3", fontsize=11 * PX, color=MUTED, labelpad=6 * PX)
    ax.set_yticks([0, 25, 50, 75, 100]); ax.set_yticklabels(["0", "25", "50", "75", "100%"])
    for key, _, col in series:
        ax.annotate(f"{lt[key]['6']:.0f}%", (6, lt[key]["6"]), xytext=(9 * PX, 0), textcoords="offset points", va="center", fontsize=11 * PX, color=INK)
    n_new = wl["lead_time"]["new_category3_entries"]
    titles(ax, "Most failures are visible months ahead", f"New Category 3 entries already on a watch list ({n_new} entries,\nJul 2024 to Jun 2026), by months of warning")
    handles = [Line2D([0], [0], color=c, linewidth=2 * PX) for _, _, c in series]
    ax.legend(handles, [n for _, n, _ in series], loc="lower left", bbox_to_anchor=(0.02, 0.03), frameon=False, fontsize=10.5 * PX, labelcolor=INK2, handlelength=1.6, labelspacing=0.45, borderaxespad=0)

    ax = axes[2]; style(ax, grid_axis="x")
    m = pd.DataFrame(ew["metrics"]).set_index("scorer"); ci = ew["bootstrap_ci"]
    rows = [("Category 2 today (flag)", "currently Category 2 (flag)", None), ("Trailing 52-week rate", "trailing 52-week rate", None), ("Positives to spare", "positives to spare (fewest first)", None),
            ("Binomial projection", "binomial projection", "auroc_proj"), ("Logistic regression", "logistic regression", "auroc_lr"), ("Gradient boosting", "gradient boosting", "auroc_gb")]
    pos = np.arange(len(rows))[::-1]; ax.set_ylim(-0.6, len(rows) - 0.4); ax.set_xlim(0.78, 0.985)
    ax.set_yticks(pos); ax.set_yticklabels([r[0] for r in rows], color=INK2); ax.set_xticks([0.80, 0.85, 0.90, 0.95]); ax.set_xticklabels(["0.80", "0.85", "0.90", "0.95"])
    for p, (_, key, cik) in zip(pos, rows):
        v = m.loc[key, "auroc"]
        if cik:
            ax.plot([ci[cik]["lo"], ci[cik]["hi"]], [p, p], color=BLUE, linewidth=2 * PX, solid_capstyle="round", zorder=2, alpha=0.45)
        ax.plot([v], [p], marker="o", markersize=10 * PX, markerfacecolor=BLUE, markeredgecolor=SURFACE, markeredgewidth=2 * PX, linestyle="none", zorder=3)
        ax.annotate(f"{v:.3f}", (ci[cik]["hi"] if cik else v, p), xytext=(8 * PX, 0), textcoords="offset points", va="center", fontsize=11 * PX, color=INK)
    titles(ax, "Simple arithmetic does most of the work", "AUROC, failing within 6 months, tested on 2024-25.\nAxis starts at 0.78. Lines are 95% intervals.")
    fig.text(0.045, 0.03, "Source: FSIS establishment-specific raw poultry sampling data and Salmonella category postings (Oct 2, 2026). A unit is one plant and product class. Preliminary analysis.",
             fontsize=9.5 * PX, color=MUTED, ha="left")
    fig.savefig(out / "figures" / "fig2_who_fails_and_how_early.png", dpi=DPI); plt.close(fig)


def fig3(out: Path) -> None:
    """FSIS's indicator serotypes against FSIS's own FY2022 to FY2026 target path. One panel, one axis."""
    t = pd.read_csv(out / "t15_fsis_indicator_serotypes_by_fy.csv"); hz = json.loads((out / "hazard_first_look.json").read_text())["fsis_indicator"]
    fig = plt.figure(figsize=(7.6, 4.9), dpi=DPI); ax = fig.add_axes([0.085, 0.215, 0.80, 0.50]); style(ax)
    yrs = t["fy"].to_numpy(); obs = t["pct"].to_numpy(); tg = t.dropna(subset=["fsis_target_pct"])
    line(ax, tg["fy"].to_numpy(), tg["fsis_target_pct"].to_numpy(), ORANGE); line(ax, yrs, obs, BLUE)
    ax.set_ylim(0, 7); ax.set_yticks([0, 2, 4, 6]); ax.set_yticklabels(["0", "2", "4", "6%"]); ax.set_xlim(2014.6, 2028.3)
    ax.set_xticks([2015, 2017, 2019, 2021, 2023, 2025]); ax.set_xticklabels(["FY15", "FY17", "FY19", "FY21", "FY23", "FY25"])
    ax.annotate(f"{obs[-1]:.1f}% observed", (yrs[-1], obs[-1]), xytext=(9 * PX, 0), textcoords="offset points", va="center", fontsize=11 * PX, color=INK)
    ax.annotate(f"{tg['fsis_target_pct'].iloc[-1]:.1f}% target", (tg["fy"].iloc[-1], tg["fsis_target_pct"].iloc[-1]), xytext=(9 * PX, 0), textcoords="offset points", va="center", fontsize=11 * PX, color=INK)
    ax.text(0, 1.42, "FSIS's indicator serotypes went up, not down", transform=ax.transAxes, fontsize=14 * PX, fontweight="bold", color=INK, va="bottom", ha="left")
    ax.text(0, 1.39, "Routine poultry samples positive for Infantis, Enteritidis or Typhimurium, by fiscal year.\n"
                     f"Target path: FSIS's FY2022 to FY2026 indicator, 10% below its {hz['fsis_stated_baseline_pct']}% baseline by FY2026.",
            transform=ax.transAxes, fontsize=11 * PX, color=INK2, va="top", ha="left", linespacing=1.3)
    legend(ax, [("Observed in the public sampling files", BLUE, None), ("FSIS target path", ORANGE, None)], y=1.04)
    p = hz["fixed_panel"]; last = str(int(yrs[-1]))
    fig.text(0.085, 0.085, f"Recomputed from routine samples (baseline {hz['baseline_recomputed']['pct']:.2f}% against FSIS's stated {hz['fsis_stated_baseline_pct']}%). FSIS's official results may differ.\n"
                           f"The same {p['units']} plant and product units sampled every year since FY2020 go from {p['baseline_fy2020_21_pct']:.1f}% to {p['pct_by_fy'][last]:.1f}%.\n"
                           "Source: FSIS raw poultry sampling data (files posted Oct 2, 2026) and FSIS's FY2022-2026 food safety indicator sheet.\n"
                           "FY2026 covers Oct 2025 to Jun 2026. Preliminary analysis.",
             fontsize=9.5 * PX, color=MUTED, ha="left", va="center", linespacing=1.35)
    fig.savefig(out / "figures" / "fig3_fsis_indicator_vs_target.png", dpi=DPI); plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--data", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(); (a.out / "figures").mkdir(parents=True, exist_ok=True)
    fig1(a.out); fig2(a.data, a.out); fig3(a.out)
    print("wrote", sorted(p.name for p in (a.out / "figures").glob("*.png")))


if __name__ == "__main__":
    main()
