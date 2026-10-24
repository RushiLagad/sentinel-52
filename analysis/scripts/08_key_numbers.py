#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-09 and run end to
# end on the real FSIS files. Review it before relying on it.
# -----------------------------------------------------------------------------
"""Collect the headline numbers into one file so every figure quoted in the README can be traced.

Usage:
  python scripts/08_key_numbers.py --data data/processed --out outputs
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--data", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(); J = lambda n: json.loads((a.out / n).read_text())
    build = json.loads((a.data / "build_report.json").read_text()); prof = J("profile_summary.json"); val = J("category_validation.json")
    ew = J("early_warning_summary_h6.json"); wl = J("watchlist_comparison_h6.json"); hz = J("hazard_first_look.json")
    S = pd.read_parquet(a.data / "samples.parquet"); agg = pd.read_parquet(a.data / "posted_aggregate.parquet"); posted = pd.read_parquet(a.data / "posted_categories.parquet")
    k: dict = {}
    k["data"] = {**build["totals"], "fiscal_years": [int(S["fy"].min()), int(S["fy"].max())], "establishments_ever_sampled": int(S["establishment_id"].nunique()),
                 "establishments_per_fy": {int(fy): int(n) for fy, n in S.groupby("fy")["establishment_id"].nunique().items()},
                 "vaccine_only_positives": build["vaccine_only_positives"], "directory_match_pct_fy2024plus": build["join_checks"]["samples_fy2024plus_with_directory_match_pct"]}
    fy = prof["routine_pct_by_fy"]
    k["routine_positivity_pct"] = {c: {y: fy[y][c] for y in ("2017", "2021", "2025", "2026")} for c in ("chicken_carcass", "chicken_parts", "comminuted_chicken", "comminuted_turkey", "turkey_carcass")}
    k["chicken_serotype_share_routine_pct"] = {y: prof["chicken_serotype_share_routine"][y] for y in ("2015", "2021", "2026")}
    k["month_range_pct"] = prof["month_range_pct"]
    k["persistence_next_year_pct"] = {r["product_class"]: {"bottom_fifth": r["next_pct_bottom_fifth"], "top_fifth": r["next_pct_top_fifth"], "spearman": r["spearman"], "pairs": r["pairs"]} for r in prof["persistence"]}
    fp = pd.DataFrame(prof["fixed_panel"]); cc = fp[fp["product_class"] == "comminuted_chicken"].set_index("fy")
    k["comminuted_chicken_mix_check"] = {"all_plants_pct": {int(y): float(v) for y, v in cc["all_pct"].items()}, "fixed_panel_pct": {int(y): float(v) for y, v in cc["panel_pct"].items()}, "fixed_panel_plants": int(cc["panel_est"].iloc[0])}
    tot_rows = sum(v["final_rule"]["joined"] for v in val.values()); tot_match = sum(v["final_rule"]["match"] for v in val.values())
    k["category_validation"] = {w: {"posted_rows": v["final_rule"]["posted_rows"], "joined": v["final_rule"]["joined"], "match_pct": v["final_rule"]["match_pct"],
                                    "cat3_recovered": f'{v["final_rule"]["posted_cat3_rebuilt_cat3"]}/{v["final_rule"]["posted_cat3"]}', "false_cat3": v["final_rule"]["rebuilt_cat3_not_posted_cat3"],
                                    "naive_percent_rule_match_pct": v["percent_rule_all_positives"]["match_pct"], "naive_false_cat3": v["percent_rule_all_positives"]["rebuilt_cat3_not_posted_cat3"]} for w, v in val.items()}
    k["category_validation"]["overall"] = {"joined": tot_rows, "match": tot_match, "match_pct": round(100 * tot_match / tot_rows, 2)}
    sz = agg[agg["haccp_size"] != "All"].groupby(["haccp_size", "category"])["establishments"].sum().unstack()
    k["latest_posting"] = {"window": agg["window_text"].iloc[0], "categories": posted["category"].value_counts().to_dict(),
                           "category3_by_size": {s: {"cat3": int(sz.loc[s, "3"]), "rated": int(sz.loc[s].sum()), "pct": round(100 * float(sz.loc[s, "3"] / sz.loc[s].sum()), 1)} for s in ("Large", "Small", "Very Small")},
                           "arkansas": {"rows": int((posted["state"] == "AR").sum()), "establishments": int(posted.loc[posted["state"] == "AR", "establishment_number"].nunique()),
                                        "categories": posted.loc[posted["state"] == "AR", "category"].value_counts().to_dict()}}
    carc = agg[(agg["product_class_posted"] == "Young Chicken Carcasses") & (agg["haccp_size"] != "All")].pivot(index="haccp_size", columns="category", values="establishments")
    k["latest_posting"]["chicken_carcass_cat3_by_size"] = {s: f'{int(carc.loc[s, "3"])} of {int(carc.loc[s].sum())}' for s in ("Large", "Small", "Very Small")}
    k["early_warning_h6"] = {"task": ew["task"], "transition_pct": ew["transition_pct"], "metrics": {m["scorer"]: {"auroc": m["auroc"], "avg_precision": m["avg_precision"], "recall_top10pct": m["recall_top10pct"], "precision_top10pct": m["precision_top10pct"]} for m in ew["metrics"]},
                             "bootstrap_ci": ew["bootstrap_ci"], "bootstrap_establishments": ew["bootstrap_establishments"], "watch_lists": wl["lists"], "lead_time": wl["lead_time"], "median_units_per_month": wl["median_units_per_month"]}
    for h in (3, 12):
        f = a.out / f"early_warning_summary_h{h}.json"
        if f.exists():
            e = json.loads(f.read_text()); k[f"early_warning_h{h}"] = {"task": e["task"], "auroc": {m["scorer"]: m["auroc"] for m in e["metrics"]}, "bootstrap_ci": {x: e["bootstrap_ci"][x] for x in ("auroc_proj", "auroc_gb", "d_auroc_gb")}}
    k["hazard"] = {"fsis_calls_overall": hz["fsis_calls_overall"], "by_serotype": {f'{r["species"]}|{r["serotype_clean"]}': {"isolates": r["isolates"], "mdr3_pct": r["mdr3_pct"], "ceftriaxone_r_pct": r["ceftriaxone_r_pct"]} for r in hz["fsis_calls_by_serotype"]},
                   "cfu_by_class": hz["cfu_by_class"], "cfu_coverage": hz["cfu_coverage"], "proposed_2024_product_standard": hz["proposed_2024_product_standard"],
                   "fsis_indicator": hz["fsis_indicator"],
                   "heuristic_vs_fsis_mdr_agree_pct": hz["heuristic_vs_fsis_mdr_agree_pct"]}
    t3 = pd.read_csv(a.out / "t3_detail_available_per_positive.csv")
    k["data"]["positives_with_serotype_pct"] = round(100 * float(t3["serotype"].sum() / t3["positives"].sum()), 2)
    C = pd.read_parquet(a.data / "cecal.parquet"); yc = C[C["slaughter_class"] == "Animal-Chicken-Young Chicken"]
    carc = set(S.loc[(S["program"] == "routine") & (S["product_class"] == "chicken_carcass"), "establishment_id"].unique())
    per_fy = yc[yc["fy"] >= 2021].groupby("fy").agg(n=("form_id", "size"), plants=("establishment_id", "nunique"))
    k["cecal_young_chicken"] = {"samples": int(len(yc)), "carcass_plants_routine": len(carc), "carcass_plants_with_cecal_samples": len(carc & set(yc["establishment_id"].unique())),
                                "plants_sampled_per_fy_since_2021": [int(per_fy["plants"].min()), int(per_fy["plants"].max())],
                                "samples_per_sampled_plant_per_fy_since_2021": [round(float((per_fy["n"] / per_fy["plants"]).min()), 1), round(float((per_fy["n"] / per_fy["plants"]).max()), 1)]}
    cm = S[(S["program"] == "routine") & (S["product_class"] == "comminuted_chicken")].groupby("fy").agg(plants=("establishment_id", "nunique"), n=("sal_result", "count"))
    k["comminuted_chicken_mix_check"]["plants_sampled"] = {int(y): int(v) for y, v in cm["plants"].items() if y >= 2022}
    k["comminuted_chicken_mix_check"]["samples_per_plant"] = {int(y): round(float(r["n"] / r["plants"]), 1) for y, r in cm.iterrows() if y >= 2022}
    (a.out / "key_numbers.json").write_text(json.dumps(k, indent=1, default=str))
    print(json.dumps({x: k[x] for x in ("data", "category_validation", "latest_posting")}, indent=1, default=str)[:3500])


if __name__ == "__main__":
    main()
