#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-27.
# -----------------------------------------------------------------------------
"""Draw the One Health system map (Task 1 deliverable) as a report figure.

The map is not decoration. It makes three claims that the rest of the project
has to honour, and drawing it is how we check that we did:

  1. Which domain each dataset belongs to, and therefore why this is One Health
     rather than food safety with extra columns.
  2. Which arrows carry the argument. Climate into production is why risk is
     seasonal rather than constant. Human burden back into population
     vulnerability is why the same contamination is not equally costly
     everywhere, and it is the link that makes the equity objective a
     consequence of the system rather than a bolt-on.
  3. Which arrow must never be drawn. Establishment to illness is forbidden by
     the FSIS licence, no code in this repository constructs it, and the figure
     shows the absence explicitly instead of leaving it to a caption. A reader
     who notices the gap should find it labelled.

Layout is hand-placed in axes coordinates rather than computed by a graph
library: there are eleven boxes and the point is legibility, not generality.

    python scripts/18_figure_system_map.py --out outputs
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

# Same palette and pixel convention as 07_figures.py, so the figures read as
# one set in the report.
SURFACE, INK, INK2, MUTED, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#c3c2b7"
BLUE, ORANGE, AQUA, DEEMPH = "#2a78d6", "#eb6834", "#1baf7a", "#b4b2aa"
PX = 72 / 100
DPI = 200

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11 * PX,
                     "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
                     "savefig.facecolor": SURFACE})

# Four One Health domains, left to right, each with its own hue so a reader can
# see at a glance that every column is represented by real data.
# Four One Health domains, left to right, each with its own hue so a reader can
# see at a glance that every column is carried by real data.
DOMAINS = [
    (0.100, "ENVIRONMENT", AQUA),
    (0.355, "ANIMAL / PRODUCTION", BLUE),
    (0.615, "FOOD", ORANGE),
    (0.875, "HUMAN", MUTED),
]

# Three rows. Keeping the geometry in named constants rather than scattered
# literals is what makes the arrows land on box edges instead of through them.
R1_Y, R1_H, R1_W = 0.725, 0.145, 0.170          # top row: the four domains
R2_Y, R2_H = 0.465, 0.115                        # what production and food feed into
R3_Y, R3_H, R3_W = 0.185, 0.115, 0.330           # who bears the consequence
R1_TOP, R1_BOT = R1_Y + R1_H / 2, R1_Y - R1_H / 2
R2_TOP, R2_BOT = R2_Y + R2_H / 2, R2_Y - R2_H / 2
R3_TOP = R3_Y + R3_H / 2
FORBIDDEN_Y = 0.862                              # routed above the row, not through it

# key: x, y, w, h, title, body, colour, source label
BOXES = {
    "climate":  (0.100, R1_Y, R1_W, R1_H, "Climate",
                 "temperature, precipitation,\nseason", AQUA, "NOAA GSOM"),
    "process":  (0.355, R1_Y, R1_W, R1_H, "Process control",
                 "FSIS sampling, serotype,\nWGS resistance", BLUE, "FSIS"),
    "lot":      (0.615, R1_Y, R1_W, R1_H, "Lot in inventory",
                 "quantity, perishability,\ndestination", ORANGE, "SIMULATED"),
    "burden":   (0.875, R1_Y, R1_W, R1_H, "Illness burden",
                 "by serotype,\nnot by plant", MUTED, "CDC NORS"),
    "category": (0.355, R2_Y, R1_W, R2_H, "FSIS category, recalls",
                 "the status quo signal", BLUE, "FSIS"),
    "decision": (0.615, R2_Y, R1_W, R2_H, "Decision",
                 "distribute · prioritize\nhold · divert", ORANGE, ""),
    "vuln":     (0.615, R3_Y, R3_W, R3_H, "Population vulnerability",
                 "SVI and food access shape who bears the consequence", MUTED, "CDC/ATSDR SVI"),
}


def box(ax, key):
    x, y, w, h, title, body, colour, src = BOXES[key]
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                boxstyle="round,pad=0.008,rounding_size=0.012",
                                linewidth=1.4 * PX, edgecolor=colour,
                                facecolor=SURFACE, zorder=3))
    ax.text(x, y + h / 2 - 0.030, title, ha="center", va="top",
            fontsize=11.5 * PX, fontweight="bold", color=INK, zorder=4)
    ax.text(x, y + h / 2 - 0.063, body, ha="center", va="top",
            fontsize=10 * PX, color=INK2, linespacing=1.35, zorder=4)
    if src:
        weight = "bold" if src == "SIMULATED" else "normal"
        ax.text(x, y - h / 2 + 0.016, src, ha="center", va="bottom",
                fontsize=8.5 * PX, color=ORANGE if src == "SIMULATED" else MUTED,
                fontweight=weight, zorder=4)


def arrow(ax, a, b, colour=AXIS, lw=1.4, style="-", rad=0.0, label=None,
          label_xy=None, label_colour=None, emphasis=False):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=11,
                                 linewidth=(2.1 if emphasis else lw) * PX,
                                 color=colour, linestyle=style,
                                 connectionstyle=f"arc3,rad={rad}",
                                 shrinkA=2, shrinkB=2, zorder=2))
    if label:
        ax.text(*label_xy, label, ha="center", va="center",
                fontsize=9.5 * PX, color=label_colour or MUTED,
                linespacing=1.3, zorder=5,
                bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.6))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path("outputs"))
    a = ap.parse_args()

    fig = plt.figure(figsize=(12.6, 7.0), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    ax.text(0.012, 0.988, "The One Health system this tool sits inside",
            fontsize=15 * PX, fontweight="bold", color=INK, va="top")
    ax.text(0.012, 0.956,
            "Every column is carried by a real public dataset except the inventory, which is simulated and labelled so throughout.",
            fontsize=11 * PX, color=INK2, va="top")

    for x, name, colour in DOMAINS:
        # Matplotlib Text has no letterspacing property, so the tracking that
        # makes these read as column headers is done by hand.
        ax.text(x, 0.912, " ".join(name), ha="center", va="bottom",
                fontsize=9.5 * PX, fontweight="bold", color=colour)
        ax.plot([x - R1_W / 2, x + R1_W / 2], [0.905, 0.905], color=colour,
                linewidth=1.6 * PX, solid_capstyle="round")

    for k in BOXES:
        box(ax, k)

    # The spine, left to right across the top row.
    arrow(ax, (0.185, R1_Y), (0.270, R1_Y), colour=AQUA, emphasis=True,
          label="seasonality", label_xy=(0.2275, R1_Y + 0.040), label_colour=AQUA)
    arrow(ax, (0.440, R1_Y), (0.530, R1_Y), colour=BLUE,
          label="mark of\ninspection", label_xy=(0.485, R1_Y + 0.044),
          label_colour=INK2)
    arrow(ax, (0.700, R1_Y), (0.790, R1_Y), colour=ORANGE)

    # Production and food drop into the decision.
    arrow(ax, (0.355, R1_BOT), (0.355, R2_TOP), colour=BLUE)
    arrow(ax, (0.440, R2_Y), (0.530, R2_Y), colour=BLUE)
    arrow(ax, (0.615, R1_BOT), (0.615, R2_TOP), colour=ORANGE)
    arrow(ax, (0.615, R2_BOT), (0.615, R3_TOP), colour=ORANGE)

    # The return arrow that makes this One Health rather than food safety.
    arrow(ax, (0.875, R1_BOT), (0.788, R3_TOP - 0.008), colour=MUTED,
          rad=-0.20, emphasis=True)
    ax.text(0.900, 0.430, "burden is a property\nof a serotype,\nnever of a plant",
            ha="left", va="center", fontsize=9.5 * PX, color=MUTED, linespacing=1.35)

    # Vulnerability feeds back into the decision: the equity objective.
    arrow(ax, (0.500, R3_TOP), (0.555, R2_BOT), colour=MUTED, style=(0, (4, 2)))
    ax.text(0.487, 0.325, "equity objective", ha="right", va="center",
            fontsize=9.5 * PX, color=MUTED)

    # The arrow we refuse to draw. Routed above the row so that it is visibly a
    # link between production and illness, and shown rather than left to a
    # caption: a reader who looks for it should find it labelled.
    for x in (0.355, 0.875):
        ax.plot([x, x], [R1_TOP, FORBIDDEN_Y], color=DEEMPH,
                linewidth=1.2 * PX, linestyle=(0, (3, 3)), zorder=1)
    ax.plot([0.355, 0.875], [FORBIDDEN_Y, FORBIDDEN_Y], color=DEEMPH,
            linewidth=1.2 * PX, linestyle=(0, (3, 3)), zorder=1)
    ax.plot([0.615], [FORBIDDEN_Y], marker="x", markersize=9 * PX,
            markeredgewidth=1.9 * PX, color=ORANGE, zorder=4)
    ax.text(0.615, FORBIDDEN_Y - 0.016,
            "never drawn: FSIS data cannot associate a plant with illness,\n"
            "so no code in this repository constructs this link",
            ha="center", va="top", fontsize=9.5 * PX, color=ORANGE, linespacing=1.35,
            bbox=dict(facecolor=SURFACE, edgecolor="none", pad=2.0), zorder=5)

    ax.text(0.012, 0.055,
            "Production reaches the food bank because the USDA mark of inspection carries the establishment number, so a pallet traces to a plant with a sampling history.\n"
            "Heavy arrows carry the argument: climate into production is why risk is seasonal rather than constant, and illness burden into population\n"
            "vulnerability is why the same contamination is not equally costly everywhere.",
            fontsize=10 * PX, color=INK2, va="bottom", linespacing=1.45)
    ax.text(0.012, 0.018,
            "Sources: NOAA NCEI GSOM · USDA FSIS raw poultry sampling, NARMS cecal, recalls · CDC NORS · CDC/ATSDR SVI 2022. "
            "Inventory simulated by 14_build_synthetic_inventory.py.",
            fontsize=8.5 * PX, color=MUTED, va="bottom")

    (a.out / "figures").mkdir(parents=True, exist_ok=True)
    p = a.out / "figures" / "fig6_one_health_system_map.png"
    fig.savefig(p, dpi=DPI); plt.close(fig)
    print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
