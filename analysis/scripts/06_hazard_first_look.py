#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-09 and run end to
# end on the real FSIS files. Review it before relying on it.
# -----------------------------------------------------------------------------
"""First look at the "what kind of Salmonella" layer: serotype, resistance genes, CFU.

The gene-to-class map below is a quick heuristic on AMRFinderPlus-style gene
names. It is checked against FSIS's own WGS-based resistance calls where those
exist (FY2024 onward), but a proper version should use the AMRFinderPlus class
table. mdsA/mdsB (intrinsic efflux) and golS/golT are ignored. Headline
resistance numbers use FSIS's calls, not the heuristic.

The last block counts how many routine positives would have met the product
standard FSIS proposed on August 7, 2024 (89 FR 64678, document 2024-16963)
and withdrew in April 2025: Salmonella at or above 10 CFU per mL or g AND a
serotype FSIS listed for that commodity. It is a description of the samples,
not a judgement on the proposal, which picked its serotypes for virulence in
FSIS's risk assessments, not for resistance. The block after that recomputes
FSIS's FY2022-2026 indicator (samples positive for Infantis, Enteritidis or
Typhimurium) from the public routine samples.

Usage:
  python scripts/06_hazard_first_look.py --data data/processed --out outputs
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

CLASS_PATTERNS = {
    "aminoglycoside": r"^(aac|aad|aph|ant|str|rmt|arm)",
    "beta_lactam": r"^bla",
    "tetracycline": r"^tet",
    "sulfonamide": r"^sul",
    "trimethoprim": r"^dfr",
    "phenicol": r"^(flo|cat|cml)",
    "quinolone": r"^(qnr|oqx|gyr[AB]_|par[CE]_)",
    "fosfomycin": r"^fos",
    "macrolide": r"^(mph|erm|ere|mef)",
    "colistin": r"^mcr",
}
IGNORE = re.compile(r"^(mds[AB]|gol[ST]|acr|ram|sox|mar)", re.I)


def classes_of(genotype) -> frozenset:
    if not isinstance(genotype, str):
        return frozenset()
    out = set()
    for g in genotype.split(","):
        g = g.strip()
        if not g or IGNORE.match(g):
            continue
        for cls, pat in CLASS_PATTERNS.items():
            if re.match(pat, g, re.I):
                out.add(cls)
    return frozenset(out)


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--data", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    I = pd.read_parquet(a.data / "sal_isolates.parquet"); S = pd.read_parquet(a.data / "samples.parquet")
    I = I[I["program"].isin(["routine"]) & I["serotype_clean"].notna() & I["product_class"].isin(["chicken_carcass", "chicken_parts", "comminuted_chicken", "turkey_carcass", "comminuted_turkey"])].copy()
    G = I[I["resistance_genotype"].notna()].copy()
    G["classes"] = G["resistance_genotype"].map(classes_of); G["n_classes"] = G["classes"].map(len)
    G["mdr3"] = G["n_classes"] >= 3
    G["esbl_ctxm65"] = G["resistance_genotype"].str.contains("blaCTX-M-65", regex=False)
    G["any_bla"] = G["classes"].map(lambda c: "beta_lactam" in c); G["quinolone"] = G["classes"].map(lambda c: "quinolone" in c)
    res: dict = {}
    R = G[(G["fy"] >= 2023)]
    top = R["serotype_clean"].value_counts().head(8).index
    t = R[R["serotype_clean"].isin(top)].groupby(["species", "serotype_clean"]).agg(isolates=("form_id", "size"), mdr3_pct=("mdr3", "mean"), ctxm65_pct=("esbl_ctxm65", "mean"), quinolone_marker_pct=("quinolone", "mean"), median_classes=("n_classes", "median")).reset_index()
    for c in ("mdr3_pct", "ctxm65_pct", "quinolone_marker_pct"): t[c] = (100 * t[c]).round(1)
    t = t[t["isolates"] >= 30].sort_values(["species", "isolates"], ascending=[True, False])
    print("Routine isolates FY2023 to FY2026, resistance markers by serotype (genotype-based, heuristic class map)\n", t.to_string(index=False))
    res["by_serotype_fy2023plus"] = t.to_dict(orient="records"); t.to_csv(a.out / "t10_resistance_markers_by_serotype.csv", index=False)
    tr = G[G["species"] == "chicken"].groupby("fy").agg(isolates=("form_id", "size"), mdr3_pct=("mdr3", "mean"), ctxm65_pct=("esbl_ctxm65", "mean")).reset_index()
    tr["mdr3_pct"] = (100 * tr["mdr3_pct"]).round(1); tr["ctxm65_pct"] = (100 * tr["ctxm65_pct"]).round(1)
    print("\nChicken, routine isolates with a resistance genotype, by FY\n", tr.to_string(index=False)); res["chicken_mdr_by_fy"] = tr.to_dict(orient="records"); tr.to_csv(a.out / "t11_chicken_mdr_by_fy.csv", index=False)

    # check the heuristic against FSIS's WGS-based calls where they exist
    wgs_cols = {"beta_lactam": ["ampicillin_resistant_wgs", "ceftriaxone_resistant_wgs", "amoxicillin_clavulanic_acid_resistant_wgs", "cefoxitin_resistant_wgs"],
                "tetracycline": ["tetracycline_resistant_wgs"], "sulfonamide": ["sulfisoxazole_resistant_wgs"],
                "aminoglycoside": ["gentamicin_resistant_wgs", "streptomycin_resistant_wgs"], "phenicol": ["chloramphenicol_resistant_wgs"]}
    W = G[G["ampicillin_resistant_wgs"].notna()].copy(); chk = []
    for cls, cols in wgs_cols.items():
        cols = [c for c in cols if c in W.columns]
        fsis = W[cols].fillna(False).any(axis=1).to_numpy(); mine = W["classes"].map(lambda c: cls in c).to_numpy()
        chk.append({"class": cls, "isolates": int(len(W)), "fsis_wgs_resistant": int(fsis.sum()), "heuristic_has_gene": int(mine.sum()), "agree_pct": round(100 * float((fsis == mine).mean()), 1)})
    CK = pd.DataFrame(chk); print("\nHeuristic gene classes vs FSIS WGS-based resistance calls (isolates that have FSIS calls)\n", CK.to_string(index=False)); res["heuristic_check"] = chk

    # the defensible version for recent years: FSIS's own WGS-based resistance calls (FY2024 onward), grouped into drug classes
    FSIS_CLASS = {"penicillins": ["ampicillin"], "beta_lactam_inhibitor_combos": ["amoxicillin_clavulanic_acid"], "cephems": ["ceftriaxone", "ceftiofur", "cefoxitin"],
                  "aminoglycosides": ["gentamicin", "kanamycin", "streptomycin"], "macrolides": ["azithromycin"], "phenicols": ["chloramphenicol"],
                  "quinolones": ["ciprofloxacin", "nalidixic_acid"], "folate_pathway": ["sulfisoxazole", "trimethoprim_sulfamethoxazole"],
                  "tetracyclines": ["tetracycline"], "carbapenems": ["meropenem"], "polymyxins": ["colistin"]}
    F = I[I["ampicillin_resistant_wgs"].notna() & (I["fy"] >= 2024)].copy()     # one stray FY2021 isolate has calls; leave it out
    for cls, drugs in FSIS_CLASS.items():
        cols = [d + "_resistant_wgs" for d in drugs if d + "_resistant_wgs" in F.columns]
        F["R_" + cls] = F[cols].fillna(False).any(axis=1)
    rc = [c for c in F.columns if c.startswith("R_")]
    F["n_classes_fsis"] = F[rc].sum(axis=1); F["mdr3_fsis"] = F["n_classes_fsis"] >= 3
    F["ceph3"] = F[["ceftriaxone_resistant_wgs"]].fillna(False).any(axis=1)
    topf = F["serotype_clean"].value_counts().head(9).index
    tf = F[F["serotype_clean"].isin(topf)].groupby(["species", "serotype_clean"]).agg(isolates=("form_id", "size"), mdr3_pct=("mdr3_fsis", "mean"), ceftriaxone_r_pct=("ceph3", "mean"),
                                                                                         quinolone_r_pct=("R_quinolones", "mean"), tetracycline_r_pct=("R_tetracyclines", "mean"), no_resistance_pct=("n_classes_fsis", lambda x: (x == 0).mean())).reset_index()
    for c in [c for c in tf.columns if c.endswith("_pct")]: tf[c] = (100 * tf[c]).round(1)
    tf = tf[tf["isolates"] >= 30].sort_values(["species", "isolates"], ascending=[True, False])
    print(f"\nFSIS WGS-based resistance calls, routine isolates FY{int(F['fy'].min())} to FY{int(F['fy'].max())} ({len(F)} isolates): resistant to 3 or more drug classes, by serotype\n", tf.to_string(index=False))
    res["fsis_calls_by_serotype"] = tf.to_dict(orient="records"); tf.to_csv(a.out / "t13_fsis_wgs_resistance_by_serotype.csv", index=False)
    res["fsis_calls_overall"] = {"isolates": int(len(F)), "fy_range": [int(F["fy"].min()), int(F["fy"].max())],
                                 "chicken_mdr3_pct": round(100 * float(F.loc[F["species"] == "chicken", "mdr3_fsis"].mean()), 1),
                                 "turkey_mdr3_pct": round(100 * float(F.loc[F["species"] == "turkey", "mdr3_fsis"].mean()), 1),
                                 "class_resistance_pct": {c[2:]: round(100 * float(F[c].mean()), 1) for c in rc}}
    print("overall:", json.dumps(res["fsis_calls_overall"]))
    cmp = F[F["resistance_genotype"].notna()].copy(); cmp["mdr3"] = cmp["resistance_genotype"].map(classes_of).map(len) >= 3
    res["heuristic_vs_fsis_mdr_agree_pct"] = round(100 * float((cmp["mdr3"] == cmp["mdr3_fsis"]).mean()), 1)
    print("heuristic MDR flag agrees with the FSIS-call MDR flag on", res["heuristic_vs_fsis_mdr_agree_pct"], "% of", len(cmp), "isolates")

    # enumeration: how often is a positive at or above 10 CFU, by product class (routine positives, FY2023+).
    # Every reported count is either "<10" or a number of 10 or more, so "10 CFU or more" means "quantifiable".
    # A few routine samples are screened Negative yet carry a "<10" count; only positives are used here.
    CFU_CLASSES = ["chicken_carcass", "chicken_parts", "comminuted_chicken", "comminuted_turkey"]      # turkey carcasses have no counts
    RP = S[(S["program"] == "routine") & (S["sal_result"] == 1) & S["product_class"].isin(CFU_CLASSES)].copy()
    RP["has_cfu"] = RP["sal_cfu_sign"].notna(); RP["d"] = pd.to_datetime(RP["collection_date"])
    Q = RP[RP["has_cfu"] & (RP["fy"] >= 2023)].copy(); Q["ge10"] = Q["sal_cfu_ge10"].astype(float)
    q = Q.groupby("product_class").agg(positives_with_cfu=("ge10", "size"), ge10_pct=("ge10", "mean")).reset_index(); q["ge10_pct"] = (100 * q["ge10_pct"]).round(1)
    allpos = RP[RP["fy"] >= 2023].groupby("product_class").size().rename("routine_positives").reset_index()
    q = q.merge(allpos, on="product_class"); q["cfu_coverage_pct"] = (100 * q["positives_with_cfu"] / q["routine_positives"]).round(1)
    print("\nEnumeration, routine positives FY2023 to FY2026\n", q.to_string(index=False)); res["cfu_by_class"] = q.to_dict(orient="records"); q.to_csv(a.out / "t12_cfu_by_product_class.csv", index=False)
    qs = Q.merge(I[["form_id", "serotype_clean"]].drop_duplicates("form_id"), on="form_id", how="left")
    qq = qs[qs["serotype_clean"].isin(["Infantis", "Kentucky", "Enteritidis", "Typhimurium", "Schwarzengrund", "Hadar", "Agona"])].groupby("serotype_clean").agg(n=("ge10", "size"), ge10_pct=("ge10", "mean")).reset_index(); qq["ge10_pct"] = (100 * qq["ge10_pct"]).round(1)
    print("\nShare of enumerated positives at 10 CFU or more, by serotype\n", qq.sort_values("n", ascending=False).to_string(index=False)); res["cfu_by_serotype"] = qq.to_dict(orient="records")

    # where counts exist: start date by product class, coverage once all classes report, and the tail with none yet
    first = RP[RP["has_cfu"]].groupby("product_class")["d"].min(); all_from = first.max(); last_cfu = RP.loc[RP["has_cfu"], "d"].max()
    steady = RP[(RP["d"] >= all_from) & (RP["d"] <= last_cfu)]; tail = RP[RP["d"] > last_cfu]
    RP["quarter"] = RP["d"].dt.to_period("Q").astype(str)
    byq = RP[RP["d"] >= first.min()].groupby("quarter")["has_cfu"].agg(["sum", "size"])
    res["cfu_coverage"] = {"first_count_by_class": {c: str(d.date()) for c, d in first.items()}, "all_classes_from": str(all_from.date()), "last_count_date": str(last_cfu.date()),
                           "coverage_pct_all_classes_from_to_last_count": round(100 * float(steady["has_cfu"].mean()), 1), "positives_in_that_span": int(len(steady)),
                           "routine_positives_after_last_count": int(len(tail)), "last_collection_date": str(RP["d"].max().date()),
                           "routine_negatives_with_a_count": int(((S["program"] == "routine") & S["sal_cfu_sign"].notna() & (S["sal_result"] != 1)).sum()),
                           "followup_positives_with_a_count_pct": round(100 * float(S[(S["program"] == "followup") & (S["sal_result"] == 1) & (S["fy"] >= 2023)]["sal_cfu_sign"].notna().mean()), 1),
                           "by_quarter_pct": {k: round(100 * float(r["sum"] / r["size"]), 1) for k, r in byq.iterrows()}}
    print("\nWhere CFU counts exist (routine positives):", json.dumps({k: v for k, v in res["cfu_coverage"].items() if k != "by_quarter_pct"}))

    # the product standard FSIS proposed in August 2024 and withdrew in April 2025: 10 CFU per mL or g or more AND a listed serotype.
    # "Typhimurium - Possible Vaccine Strain" is a separate label in the data and is not counted as listed.
    LISTED = {"chicken": {"Enteritidis", "Typhimurium", "I 4,[5],12:i:-"}, "turkey": {"Hadar", "Typhimurium", "Muenchen"}}
    sero = I.groupby("form_id")["serotype_clean"].agg(frozenset)                 # a sample can have two isolates
    Z = RP[RP["has_cfu"]].copy(); Z["sero"] = Z["form_id"].map(sero); Z = Z[Z["sero"].notna()].copy()
    Z["species"] = np.where(Z["product_class"] == "comminuted_turkey", "turkey", "chicken")
    Z["ge10"] = Z["sal_cfu_ge10"].astype(bool); Z["listed"] = [bool(s & LISTED[sp]) for s, sp in zip(Z["sero"], Z["species"])]; Z["both"] = Z["ge10"] & Z["listed"]
    def _row(d: pd.DataFrame) -> dict:
        return {"positives_with_count_and_serotype": int(len(d)), "ge10_pct": round(100 * float(d["ge10"].mean()), 1), "listed_serotype_pct": round(100 * float(d["listed"].mean()), 1),
                "both_pct": round(100 * float(d["both"].mean()), 1), "both_n": int(d["both"].sum())}
    ps = pd.DataFrame([{"group": c, **_row(Z[Z["product_class"] == c])} for c in CFU_CLASSES] + [{"group": "all_chicken", **_row(Z[Z["species"] == "chicken"])}])
    ps.to_csv(a.out / "t14_proposed_2024_product_standard.csv", index=False)
    print(f"\nRoutine positives that would have met the product standard proposed in 2024 (collected {Z['d'].min().date()} to {Z['d'].max().date()})\n", ps.to_string(index=False))
    # how the proposed standard and resistance overlap: chicken positives that have a count, a serotype and FSIS resistance calls (FY2024 onward)
    fm = F.groupby("form_id").agg(mdr3=("mdr3_fsis", "max"), infantis=("serotype_clean", lambda x: bool((x == "Infantis").any())))
    C = Z[(Z["species"] == "chicken")].merge(fm, left_on="form_id", right_index=True, how="inner"); M = C[C["mdr3"]]
    res["proposed_2024_product_standard"] = {
        "definition": "Salmonella at or above 10 CFU per mL or g AND a listed serotype (chicken: Enteritidis, Typhimurium, I 4,[5],12:i:-; comminuted turkey: Hadar, Typhimurium, Muenchen)",
        "collected": [str(Z["d"].min().date()), str(Z["d"].max().date())], "by_group": ps.to_dict(orient="records"),
        "chicken_with_resistance_calls": {"positives": int(len(C)), "fy_range": [int(C["fy"].min()), int(C["fy"].max())], "mdr3_pct": round(100 * float(C["mdr3"].mean()), 1),
                                          "would_have_met_pct": round(100 * float(C["both"].mean()), 1), "mdr3_pct_among_met": round(100 * float(C.loc[C["both"], "mdr3"].mean()), 1),
                                          "mdr3_pct_among_not_met": round(100 * float(C.loc[~C["both"], "mdr3"].mean()), 1), "mdr3_positives": int(len(M)),
                                          "mdr3_positives_that_met_pct": round(100 * float(M["both"].mean()), 1), "mdr3_positives_that_met_n": int(M["both"].sum()),
                                          "mdr3_positives_that_are_infantis_pct": round(100 * float(M["infantis"].mean()), 1), "mdr3_positives_at_ge10_pct": round(100 * float(M["ge10"].mean()), 1),
                                          "mdr3_positives_with_listed_serotype_pct": round(100 * float(M["listed"].mean()), 1)}}
    print("overlap with resistance (chicken):", json.dumps(res["proposed_2024_product_standard"]["chicken_with_resistance_calls"]))

    # FSIS's own indicator for FY2022 to FY2026 (USDA food safety key performance indicator): the share of poultry verification
    # samples, from products that have a performance standard, positive for the serotypes most often tied to human illness
    # (Infantis, Enteritidis, Typhimurium). FSIS states a baseline of 4.22% from FY2020-21 data and a target of 2% lower each year,
    # 10% lower by FY2026. Recomputed here from routine samples in the public files; FSIS's official yearly results may differ.
    IND = {"Infantis", "Enteritidis", "Typhimurium"}; FSIS_BASELINE = 4.22; CUT = {2022: 0.02, 2023: 0.04, 2024: 0.06, 2025: 0.08, 2026: 0.10}
    K = S[(S["program"] == "routine") & S["sal_result"].notna()].copy(); ks = K["form_id"].map(sero); is_pos = (K["sal_result"] == 1).to_numpy()
    K["ind"] = is_pos & np.array([isinstance(s, frozenset) and bool(s & IND) for s in ks])
    K["ind_v"] = is_pos & np.array([isinstance(s, frozenset) and bool(s & (IND | {"Typhimurium - Possible Vaccine Strain"})) for s in ks])
    by = K.groupby("fy").agg(samples=("ind", "size"), indicator_positives=("ind", "sum"), with_possible_vaccine_strains=("ind_v", "sum"))
    by["pct"] = 100 * by["indicator_positives"] / by["samples"]; by["pct_with_possible_vaccine_strains"] = 100 * by["with_possible_vaccine_strains"] / by["samples"]
    by["fsis_target_pct"] = [FSIS_BASELINE * (1 - CUT[y]) if y in CUT else np.nan for y in by.index]
    base = K[K["fy"].isin([2020, 2021])]; base_pct = 100 * float(base["ind"].mean())
    w = base["product_class"].value_counts(normalize=True); rc_ = K.groupby(["fy", "product_class"])["ind"].mean().unstack()
    by["pct_at_fy2020_21_product_mix"] = 100 * (rc_[w.index] * w).sum(axis=1, min_count=len(w))
    cnt = K[K["fy"] >= 2020].groupby(["establishment_id", "product_class", "fy"]).size().unstack(fill_value=0); keep = cnt[(cnt >= 10).all(axis=1)].index
    PN = K[pd.MultiIndex.from_frame(K[["establishment_id", "product_class"]]).isin(keep)]
    gp = PN.groupby("fy").agg(panel_samples=("ind", "size"), panel_pct=("ind", "mean")); by["panel_pct"] = 100 * gp["panel_pct"]; by["panel_samples"] = gp["panel_samples"]
    K["month"] = pd.to_datetime(K["collection_date"]).dt.month; by["pct_oct_to_jun_only"] = 100 * K[~K["month"].isin([7, 8, 9])].groupby("fy")["ind"].mean()
    CH = K[K["product_class"].isin(["chicken_carcass", "chicken_parts", "comminuted_chicken"])]; chs = CH["form_id"].map(sero); chpos = (CH["sal_result"] == 1).to_numpy()
    for s_ in sorted(IND):
        by["chicken_pct_" + s_.lower()] = 100 * pd.Series(chpos & np.array([isinstance(x, frozenset) and s_ in x for x in chs]), index=CH.index).groupby(CH["fy"]).mean()
    t15 = by.reset_index().round(3); t15.to_csv(a.out / "t15_fsis_indicator_serotypes_by_fy.csv", index=False)
    print(f"\nFSIS indicator serotypes (Infantis, Enteritidis, Typhimurium), % of routine samples. Baseline FY2020-21 recomputed {base_pct:.2f}% (FSIS states {FSIS_BASELINE}%)\n",
          t15[["fy", "samples", "indicator_positives", "pct", "fsis_target_pct", "pct_at_fy2020_21_product_mix", "panel_pct", "pct_oct_to_jun_only"]].round(2).to_string(index=False))
    last = int(by.index.max()); pb = float(by.loc[[2020, 2021], "panel_pct"].mul(by.loc[[2020, 2021], "panel_samples"]).sum() / by.loc[[2020, 2021], "panel_samples"].sum())
    res["fsis_indicator"] = {
        "serotypes": sorted(IND), "fsis_stated_baseline_pct": FSIS_BASELINE, "fsis_target_cut_by_fy": CUT,
        "baseline_recomputed": {"fy": [2020, 2021], "indicator_positives": int(base["ind"].sum()), "samples": int(len(base)), "pct": round(base_pct, 2)},
        "pct_by_fy": {int(y): round(float(v), 2) for y, v in by["pct"].items()}, "fsis_target_pct_by_fy": {int(y): round(float(v), 2) for y, v in by["fsis_target_pct"].dropna().items()},
        "change_vs_recomputed_baseline_pct": {int(y): round(100 * (float(by.loc[y, "pct"]) / base_pct - 1), 1) for y in by.index if y >= 2022},
        "pct_at_fy2020_21_product_mix": {int(y): round(float(v), 2) for y, v in by["pct_at_fy2020_21_product_mix"].items() if y >= 2020},
        "fixed_panel": {"units": int(len(keep)), "establishments": int(len({k_[0] for k_ in keep})), "rule": "plant and product class with at least 10 routine samples in every fiscal year from FY2020",
                        "pct_by_fy": {int(y): round(float(v), 2) for y, v in by["panel_pct"].items() if y >= 2020}, "baseline_fy2020_21_pct": round(pb, 2),
                        "change_vs_panel_baseline_pct": {int(y): round(100 * (float(by.loc[y, "panel_pct"]) / pb - 1), 1) for y in by.index if y >= 2022}},
        "pct_oct_to_jun_only": {int(y): round(float(v), 2) for y, v in by["pct_oct_to_jun_only"].items() if y >= 2020},
        "pct_with_possible_vaccine_strains": {int(y): round(float(v), 2) for y, v in by["pct_with_possible_vaccine_strains"].items() if y >= 2020},
        "chicken_samples_pct_by_serotype": {s_: {int(y): round(float(v), 2) for y, v in by["chicken_pct_" + s_.lower()].items() if y in (2021, 2025, last)} for s_ in sorted(IND)},
        "last_fy_is_partial": bool(pd.to_datetime(K.loc[K["fy"] == last, "collection_date"]).max().month != 9)}
    print("indicator summary:", json.dumps({k_: v for k_, v in res["fsis_indicator"].items() if k_ in ("baseline_recomputed", "change_vs_recomputed_baseline_pct", "fixed_panel")}))
    (a.out / "hazard_first_look.json").write_text(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
    main()
