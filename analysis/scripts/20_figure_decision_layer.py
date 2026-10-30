#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-30.
# -----------------------------------------------------------------------------
"""Two report figures from the decision layer (Task 3), read from the tables
16_decision_layer.py writes so they cannot disagree with the text.

  fig7  The frontier: how much food goes out uncooked against how much of the
        truly elevated risk the policy catches, as the hold threshold sweeps.
        The four named scenarios sit on or near that curve as labelled points.
        The point of the picture is that the curve bends: the first holds are
        cheap in food and the last ones are expensive, and the status quo rule
        sits far off the curve because it holds on category alone.

  fig8  What each scenario costs in the two quantities a food bank actually
        argues about: meals lost that a better-aimed policy would have moved,
        and meals that went out uncooked from plants that later went on to
        elevated risk. Same four scenarios, same colours, two separate axes.

Pounds are synthetic throughout (14_build_synthetic_inventory.py) and both
figures say so on the axis. Recall and precision are real, because they come
from the FSIS test period.

    python scripts/20_figure_decision_layer.py --out outputs --horizon 3
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

# Same palette and pixel convention as 07_figures.py and 18_figure_system_map.py.
SURFACE, INK, INK2, MUTED, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#c3c2b7"
BLUE, ORANGE, VIOLET, GREEN = "#2a78d6", "#eb6834", "#8257d6", "#178f63"
PX = 72 / 100
DPI = 200

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11 * PX,
                     "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
                     "savefig.facecolor": SURFACE, "axes.edgecolor": AXIS,
                     "xtick.color": INK2, "ytick.color": INK2,
                     "axes.labelcolor": INK2, "text.color": INK})

# Fixed colour per scenario, in the order the report discusses them. The
# order never changes with the data, so the same scenario is the same colour
# in every figure and in the app.
SCEN = [
    ("rule_based_category",    "Rule-based (status quo)",   MUTED),
    ("conservative",           "Conservative",              BLUE),
    ("capacity_matched",       "Capacity-matched",          ORANGE),
    ("food_security_weighted", "Food-security weighted",    VIOLET),
]


def tidy(ax) -> None:
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=AXIS, linewidth=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def frontier_figure(fr: pd.DataFrame, sc: pd.DataFrame, out: Path, h: str) -> Path:
    fig, ax = plt.subplots(figsize=(9.6, 5.6), dpi=DPI)
    tidy(ax)
    ax.grid(axis="x", color=AXIS, linewidth=0.6, alpha=0.6)

    x = fr["pounds_distributed"] / 1e6
    ax.plot(x, fr["recall"], color=INK2, linewidth=2 * PX * 1.4, zorder=2)
    ax.scatter(x, fr["recall"], s=18, color=SURFACE, edgecolor=INK2, linewidth=1.2, zorder=3)
    # label the ends of the sweep so the reader knows which way the threshold runs
    lo, hi = fr.iloc[0], fr.iloc[-1]
    ax.annotate(f"hold at {lo.hold_at:.2f}", (lo.pounds_distributed / 1e6, lo.recall),
                xytext=(-10, 22), textcoords="offset points", ha="right", color=INK2, fontsize=9 * PX)
    ax.annotate(f"hold at {hi.hold_at:.2f}", (hi.pounds_distributed / 1e6, hi.recall),
                xytext=(6, -12), textcoords="offset points", ha="left", color=INK2, fontsize=9 * PX)

    # The three model-based scenarios sit within a few hundred thousand pounds
    # of each other, so their labels are placed by hand in axes coordinates and
    # tied to the points with leader lines. Letting matplotlib stack them
    # produced overprinting.
    TEXT_AT = {
        "rule_based_category":    (0.06, 0.86, "left"),
        "conservative":           (0.44, 0.62, "left"),
        "capacity_matched":       (0.30, 0.18, "left"),
        "food_security_weighted": (0.72, 0.18, "left"),
    }
    for key, label, col in SCEN:
        r = sc.loc[sc.scenario == key].iloc[0]
        px, py = r.pounds_distributed / 1e6, r.recall
        ax.scatter([px], [py], s=110, color=col, edgecolor=SURFACE, linewidth=2, zorder=5)
        tx, ty, ha = TEXT_AT[key]
        ax.annotate(f"{label}\nrecall {py:.2f}, precision {r.precision:.2f}\n{r.holds_per_week_required:.1f} holds per week",
                    (px, py), xytext=(tx, ty), textcoords="axes fraction", ha=ha, va="center",
                    fontsize=9.5 * PX, color=INK, linespacing=1.2,
                    arrowprops=dict(arrowstyle="-", color=col, linewidth=1.1, shrinkB=7,
                                    connectionstyle="arc3,rad=0.0"))

    ax.set_xlabel("Pounds distributed uncooked over the test period, millions (synthetic inventory)")
    ax.set_ylabel(f"Recall: share of plants that went on to elevated risk\nwhose lots were held or diverted ({h}-month horizon)")
    ax.set_ylim(0, 1.08)
    ax.set_title("Food out against risk caught: the hold-threshold sweep and the four named scenarios",
                 loc="left", fontsize=12.5 * PX, color=INK, pad=10)
    ax.text(0, -0.2, "Sweep: hold threshold 0.02 to 0.30 with divert at 2.5x hold. Status quo holds on FSIS category alone, "
            "so it catches everything and sends the least food.",
            transform=ax.transAxes, fontsize=9 * PX, color=MUTED, va="top")
    fig.tight_layout()
    p = out / "figures" / f"fig7_frontier_h{h}.png"
    fig.savefig(p, dpi=DPI)
    plt.close(fig)
    return p


def cost_figure(sc: pd.DataFrame, out: Path, h: str) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.2), dpi=DPI, sharey=True)
    order = [k for k, _, _ in SCEN]
    sc = sc.set_index("scenario").loc[order]
    labels = [l for _, l, _ in SCEN]
    cols = [c for _, _, c in SCEN]
    y = range(len(order))[::-1]

    panels = [
        (axes[0], sc["avoidable_loss_meals"] / 1e3,
         "Meals lost that a better-aimed policy\nwould have moved (thousands)"),
        (axes[1], sc["exposure_meals"] / 1e3,
         "Meals distributed uncooked from plants that\nwent on to elevated risk (thousands)"),
    ]
    for ax, vals, title in panels:
        tidy(ax)
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", color=AXIS, linewidth=0.6, alpha=0.6)
        ax.barh(list(y), vals.values, color=cols, height=0.62, edgecolor=SURFACE, linewidth=2)
        for yy, v in zip(y, vals.values):
            ax.text(v + vals.max() * 0.015, yy, f"{v:,.0f}", va="center", fontsize=9.5 * PX, color=INK)
        ax.set_xlim(0, vals.max() * 1.18)
        ax.set_title(title, loc="left", fontsize=11 * PX, color=INK, pad=8)
        ax.set_xlabel("thousand meals at 1.2 lb per meal (synthetic pounds)")
    axes[0].set_yticks(list(y))
    axes[0].set_yticklabels([f"{l}\nrecall {sc.loc[k, 'recall']:.2f}" for k, l, _ in SCEN])
    fig.suptitle(f"What each scenario costs at the {h}-month horizon",
                 x=0.01, ha="left", fontsize=12.5 * PX, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    p = out / "figures" / f"fig8_scenario_costs_h{h}.png"
    fig.savefig(p, dpi=DPI)
    plt.close(fig)
    return p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("outputs"))
    ap.add_argument("--horizon", default="3")
    a = ap.parse_args()
    h = a.horizon
    sc = pd.read_csv(a.out / f"t20_scenarios_h{h}.csv")
    fr = pd.read_csv(a.out / f"t22_frontier_h{h}.csv")
    (a.out / "figures").mkdir(parents=True, exist_ok=True)
    for p in (frontier_figure(fr, sc, a.out, h), cost_figure(sc, a.out, h)):
        print(f"wrote {p}")


if __name__ == "__main__":
    main()
