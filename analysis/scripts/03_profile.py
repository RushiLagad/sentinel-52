#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-09 and run end to
# end on the real FSIS files. Review it before relying on it.
# -----------------------------------------------------------------------------
"""Descriptive profile of the FSIS raw poultry sampling data.

Writes CSV tables to --out and prints a compact summary. Everything about
prevalence uses ROUTINE samples only (project codes HC_*), because follow-up and
special projects are targeted at establishments that already failed.

Usage:
  python scripts/03_profile.py --data data/processed --out outputs
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

CLASSES = ["chicken_carcass", "chicken_parts", "comminuted_chicken", "turkey_carcass", "comminuted_turkey"]


def rate_table(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    g = df.groupby(by, observed=True)["sal_result"].agg(n="count", pos="sum").reset_index()
    g["pct"] = (100 * g["pos"] / g["n"]).round(2)
    return g


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--data", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    S = pd.read_parquet(a.data / "samples.parquet"); I = pd.read_parquet(a.data / "sal_isolates.parquet"); E = pd.read_parquet(a.data / "establishments.parquet")
    S = S[S["sal_result"].notna()].copy(); S["sal_result"] = S["sal_result"].astype(int)
    R = S[S["program"] == "routine"].copy()
    summary: dict = {}

    # 1. routine positivity by fiscal year and product class
    t1 = rate_table(R, ["fy", "product_class"]); t1.to_csv(a.out / "t1_routine_positivity_by_fy.csv", index=False)
    wide = t1.pivot(index="fy", columns="product_class", values="pct")[CLASSES]
    print("\n[1] Routine Salmonella % positive by fiscal year (FY2026 = Oct 2025 to Jun 2026)\n", wide.to_string())
    summary["routine_pct_by_fy"] = {int(k): {c: (None if pd.isna(v) else float(v)) for c, v in row.items()} for k, row in wide.iterrows()}

    # 2. serotype mix among routine + follow-up chicken isolates, by FY (vaccine strains kept separate)
    Ic = I[(I["species"] == "chicken") & I["serotype_clean"].notna() & I["program"].isin(["routine", "followup"])].copy()
    tot = Ic.groupby("fy").size()
    top = Ic["serotype_clean"].value_counts().head(8).index.tolist()
    t2 = (Ic[Ic["serotype_clean"].isin(top)].groupby(["fy", "serotype_clean"]).size().unstack(fill_value=0).div(tot, axis=0) * 100).round(1)
    t2["n_isolates"] = tot; t2.to_csv(a.out / "t2_chicken_serotype_share_by_fy.csv")
    print("\n[2] Share of serotyped chicken isolates (%), routine + follow-up\n", t2.to_string())
    # same, routine only, to check that follow-up sampling is not driving the shift
    Ir = Ic[Ic["program"] == "routine"]; totr = Ir.groupby("fy").size()
    t2r = (Ir[Ir["serotype_clean"].isin(["Infantis", "Kentucky", "Enteritidis", "Typhimurium"])].groupby(["fy", "serotype_clean"]).size().unstack(fill_value=0).div(totr, axis=0) * 100).round(1)
    t2r.to_csv(a.out / "t2b_chicken_serotype_share_routine_only.csv")
    print("\n[2b] Same, routine samples only\n", t2r.to_string())
    summary["chicken_serotype_share_routine"] = {int(k): {c: float(v) for c, v in row.items()} for k, row in t2r.iterrows()}

    # 3. how much genomic / AMR / enumeration detail each positive carries
    pos = S[S["sal_result"] == 1].groupby("fy").size().rename("positives")
    g = I.groupby("fy").agg(isolates=("form_id", "size"), serotype=("serotype_clean", lambda s: s.notna().sum()), sra=("sra_accession_number", lambda s: s.notna().sum()),
                            resistance_genotype=("resistance_genotype", lambda s: s.notna().sum()), virulence_genotype=("virulence_genotype", lambda s: s.notna().sum()),
                            mlst=("multi_locus_sequence", lambda s: s.notna().sum()), ast_phenotype=("ampicillin_mic", lambda s: s.notna().sum()))
    cfu = S[S["sal_cfu_sign"].notna()].groupby("fy").agg(cfu_reported=("sal_cfu_sign", "size"), cfu_ge10=("sal_cfu_ge10", "sum"))
    t3 = pd.concat([pos, g, cfu], axis=1).fillna(0).astype(int); t3["cfu_ge10_pct"] = (100 * t3["cfu_ge10"] / t3["cfu_reported"].replace(0, np.nan)).round(1)
    t3.to_csv(a.out / "t3_detail_available_per_positive.csv"); print("\n[3] Detail available per positive, by FY\n", t3.to_string())

    # 4. seasonality (routine, FY2016+)
    R16 = R[R["fy"] >= 2016].copy(); R16["month"] = R16["collection_date"].dt.month
    t4 = rate_table(R16, ["product_class", "month"]).pivot(index="month", columns="product_class", values="pct")[CLASSES]
    t4.to_csv(a.out / "t4_routine_positivity_by_month.csv"); print("\n[4] Routine % positive by calendar month, FY2016+\n", t4.to_string())
    summary["month_range_pct"] = {c: [float(t4[c].min()), float(t4[c].max())] for c in CLASSES}

    # 5. establishment persistence: rank by this FY's rate, look at next FY's rate
    rows = []
    for cls in CLASSES:
        min_n = 20 if cls in ("chicken_carcass", "chicken_parts") else 10
        ep = R[R["product_class"] == cls].groupby(["establishment_id", "fy"])["sal_result"].agg(n="count", pos="sum").reset_index()
        nxt = ep.assign(fy=ep["fy"] - 1).rename(columns={"n": "n_next", "pos": "pos_next"})
        pr = ep.merge(nxt, on=["establishment_id", "fy"]); pr = pr[(pr["n"] >= min_n) & (pr["n_next"] >= min_n) & (pr["fy"].between(2016, 2024))].copy()
        pr["rate"] = pr["pos"] / pr["n"]; pr["rate_next"] = pr["pos_next"] / pr["n_next"]
        pr["q"] = pr.groupby("fy")["rate"].transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=[1, 2, 3, 4, 5])).astype(int)
        agg = pr.groupby("q").agg(n_next=("n_next", "sum"), pos_next=("pos_next", "sum")); agg["pct_next"] = 100 * agg["pos_next"] / agg["n_next"]
        rows.append({"product_class": cls, "pairs": len(pr), "spearman": round(float(pr["rate"].corr(pr["rate_next"], method="spearman")), 3),
                     "next_pct_bottom_fifth": round(float(agg.loc[1, "pct_next"]), 1), "next_pct_middle": round(float(100 * agg.loc[[2, 3, 4], "pos_next"].sum() / agg.loc[[2, 3, 4], "n_next"].sum()), 1),
                     "next_pct_top_fifth": round(float(agg.loc[5, "pct_next"]), 1), "next_pct_all": round(float(100 * pr["pos_next"].sum() / pr["n_next"].sum()), 1)})
    t5 = pd.DataFrame(rows); t5.to_csv(a.out / "t5_establishment_persistence.csv", index=False)
    print("\n[5] Persistence: establishments ranked by one FY's rate, positivity the following FY (pairs FY2016-17 through FY2024-25)\n", t5.to_string(index=False))
    summary["persistence"] = rows

    # 6. composition check: all routine samples vs a fixed panel of establishments sampled >=10 times every FY 2021-2026
    out6 = []
    for cls in CLASSES:
        d = R[(R["product_class"] == cls) & (R["fy"] >= 2021)]
        cnt = d.groupby(["establishment_id", "fy"]).size().unstack(fill_value=0)
        panel = cnt.index[(cnt >= 10).all(axis=1)] if cnt.shape[1] == 6 else []
        for fy, dd in d.groupby("fy"):
            pp = dd[dd["establishment_id"].isin(panel)]
            out6.append({"product_class": cls, "fy": int(fy), "all_est": dd["establishment_id"].nunique(), "all_n": len(dd), "all_pct": round(100 * dd["sal_result"].mean(), 1),
                         "panel_est": len(panel), "panel_n": len(pp), "panel_pct": round(100 * pp["sal_result"].mean(), 1) if len(pp) else None})
    t6 = pd.DataFrame(out6); t6.to_csv(a.out / "t6_fixed_panel_check.csv", index=False)
    print("\n[6] All establishments vs fixed panel (>=10 routine samples in every FY 2021-2026)\n", t6[t6["product_class"].isin(["comminuted_chicken", "chicken_parts", "chicken_carcass"])].to_string(index=False))
    summary["fixed_panel"] = out6

    # 7. establishment size (HACCP size from the current MPI directory) and routine positivity, FY2023+
    M = R[R["fy"] >= 2023].merge(E[["establishment_id", "haccp_size", "slaughter_volume_category", "inspection_system_npis"]], on="establishment_id", how="left")
    t7 = rate_table(M.assign(haccp_size=M["haccp_size"].fillna("unknown")), ["product_class", "haccp_size"])
    t7e = M.assign(haccp_size=M["haccp_size"].fillna("unknown")).groupby(["product_class", "haccp_size"])["establishment_id"].nunique().rename("establishments").reset_index()
    t7 = t7.merge(t7e, on=["product_class", "haccp_size"]); t7.to_csv(a.out / "t7_positivity_by_haccp_size.csv", index=False)
    print("\n[7] Routine % positive by HACCP size, FY2023 to FY2026\n", t7.to_string(index=False))
    summary["by_size"] = t7.to_dict(orient="records")

    # 8. states: routine chicken samples FY2025-26
    C = R[(R["fy"] >= 2025) & (R["species"] == "chicken")]
    t8 = C.groupby("establishment_state").agg(establishments=("establishment_id", "nunique"), n=("sal_result", "count"), pos=("sal_result", "sum")).reset_index()
    t8["pct"] = (100 * t8["pos"] / t8["n"]).round(1); t8 = t8.sort_values("n", ascending=False); t8.to_csv(a.out / "t8_states_chicken_fy2025_26.csv", index=False)
    print("\n[8] Routine chicken samples by state, FY2025-26 (top 10 by volume)\n", t8.head(10).to_string(index=False))
    summary["top_states"] = t8.head(10).to_dict(orient="records")

    # 9. sampling density per establishment per FY
    dens = R.groupby(["product_class", "fy", "establishment_id"]).size().rename("n").reset_index()
    t9 = dens.groupby(["product_class", "fy"])["n"].agg(establishments="count", median="median", p25=lambda s: s.quantile(.25), p75=lambda s: s.quantile(.75)).reset_index()
    t9.to_csv(a.out / "t9_sampling_density.csv", index=False)
    print("\n[9] Routine samples per establishment per FY (median), FY2021+\n", t9[t9["fy"] >= 2021].pivot(index="fy", columns="product_class", values="median")[CLASSES].to_string())

    summary["totals"] = {"samples_with_result": int(len(S)), "positives": int(S["sal_result"].sum()), "routine_samples": int(len(R)), "establishments": int(S["establishment_id"].nunique())}
    (a.out / "profile_summary.json").write_text(json.dumps(summary, indent=1, default=str))


if __name__ == "__main__":
    pd.set_option("display.width", 220); pd.set_option("display.max_columns", 40)
    main()
