#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-09 and run end to
# end on the real FSIS files. Review it before relying on it.
# -----------------------------------------------------------------------------
"""Fair comparison of watch lists, and how much warning each one gives.

FSIS's own Category 2 is already a warning list. The honest question is whether
a projection does better AT THE SAME LIST SIZE, and what a shorter list costs.

Reads the monthly panel written by 05_early_warning_baseline.py.

Usage:
  python scripts/05b_watchlist_comparison.py --data data/processed --out outputs --horizon 6
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--horizon", type=int, default=6); ap.add_argument("--test-start", default="2024-01-01")
    a = ap.parse_args(); H = a.horizon
    P = pd.read_parquet(a.data / f"panel_monthly_h{H}.parquet")
    D = P[P["category"].isin(["1", "2"]) & P["horizon_complete"] & P["rated_in_horizon"] & (P["window_end"] >= a.test_start)].copy()
    D["is2"] = D["category"] == "2"; D["k"] = D.groupby("window_end")["is2"].transform("sum")
    D["rk"] = D.groupby("window_end")["projection"].rank(method="first", ascending=False); D["proj_same_size"] = D["rk"] <= D["k"]
    D["k10"] = np.ceil(D.groupby("window_end")["projection"].transform("size") * 0.10); D["proj_top10"] = D["rk"] <= D["k10"]
    out = {"horizon_months": H, "rows": int(len(D)), "events": int(D["y"].sum()), "category2_list_share_pct": round(100 * float(D["is2"].mean()), 1), "lists": {}}
    for col, name in [("is2", "category_2_flag"), ("proj_same_size", "projection_same_size"), ("proj_top10", "projection_top10pct")]:
        out["lists"][name] = {"share_of_rated_units_pct": round(100 * float(D[col].mean()), 1), "precision_pct": round(100 * float(D.loc[D[col], "y"].mean()), 1),
                              "recall_pct": round(100 * float(D.loc[D[col], "y"].sum() / D["y"].sum()), 1)}

    # lead time: for each NEW Category 3 entry, the earliest month (within H) the unit was already on each list
    A = P[(P["window_end"] >= a.test_start) & P["category"].isin(["1", "2"])].copy()
    A["is2"] = A["category"] == "2"; A["k"] = A.groupby("window_end")["is2"].transform("sum")
    A["rk"] = A.groupby("window_end")["projection"].rank(method="first", ascending=False); A["proj_same_size"] = A["rk"] <= A["k"]
    A["k10"] = np.ceil(A.groupby("window_end")["projection"].transform("size") * 0.10); A["proj_top10"] = A["rk"] <= A["k10"]
    ends = sorted(P["window_end"].unique()); pos_of = {e: i for i, e in enumerate(ends)}
    first_test = [e for e in ends if e >= pd.Timestamp(a.test_start)]
    allc = P[P["window_end"] >= ends[max(0, pos_of[first_test[0]] - 1)]][["u", "window_end", "category"]].sort_values(["u", "window_end"])
    allc["prev"] = allc.groupby("u")["category"].shift(1)
    onset = allc[(allc["category"] == "3") & allc["prev"].isin(["1", "2", "NA"]) & (allc["window_end"] >= first_test[H])]
    Aidx = A.set_index(["u", "window_end"]); rows = []
    for u, e, prev in zip(onset["u"], onset["window_end"], onset["prev"]):
        i = pos_of[e]; r = {"u": u, "onset": e, "prev": prev}
        for col in ("is2", "proj_same_size", "proj_top10"):
            lead = 0
            for back in range(1, H + 1):
                key = (u, ends[i - back])
                if key in Aidx.index and bool(Aidx.loc[key, col]):
                    lead = back
            r[col] = lead
        rows.append(r)
    L = pd.DataFrame(rows)
    u2e = P.drop_duplicates("u").set_index("u")["establishment_id"]
    out["lead_time"] = {"new_category3_entries": int(len(L)), "distinct_establishments": int(L["u"].map(u2e).nunique()), "entered_from_unrated": int((L["prev"] == "NA").sum()),
                        "onset_window_ends": [str(L["onset"].min().date()), str(L["onset"].max().date())], "on_list_at_least_k_months_before_pct": {}}
    for col, name in [("is2", "category_2_flag"), ("proj_same_size", "projection_same_size"), ("proj_top10", "projection_top10pct")]:
        out["lead_time"]["on_list_at_least_k_months_before_pct"][name] = {str(k): round(100 * float((L[col] >= k).mean()), 1) for k in range(1, H + 1)}
    out["median_units_per_month"] = {"rated_1_or_2": float(A.groupby("window_end").size().median()), "category_2_flag": float(A.groupby("window_end")["is2"].sum().median()),
                                     "projection_top10pct": float(A.groupby("window_end")["k10"].first().median())}
    (a.out / f"watchlist_comparison_h{H}.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
