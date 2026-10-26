#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-26. Review before
# relying on it.
# -----------------------------------------------------------------------------
"""Compare what FSIS sampling FINDS in poultry with what actually puts people in hospital.

FSIS verification sampling measures serotype prevalence in the supply. NORS measures
outbreak-associated human illness. They are not the same ranking, and the gap is the
reason a targeting tool should weight by burden rather than by positivity alone.

Scope limits that are deliberate and must survive into the report:
  * Joins happen at SEROTYPE x YEAR only. The FSIS licence forbids linking individual
    establishments to illness outbreaks, so no establishment identifier touches NORS.
  * Outbreak-associated illness is a small and biased slice of all salmonellosis. Most
    cases are sporadic and never appear here.
  * IFSAC food attribution is missing for most Salmonella foodborne outbreaks. The
    script reports that gap rather than hiding it.

Usage:
  python scripts/10_burden_weighting.py --nors data/nors --out outputs
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

# FSIS FY2022-2026 Salmonella KPI serotypes (poultry verification samples).
KPI = {"Enteritidis", "Typhimurium", "Infantis"}
# Serotypes of public health significance in the August 2024 proposed framework,
# withdrawn in 2025 (89 FR 64678).
FRAMEWORK_2024 = {
    "Chicken": {"Enteritidis", "Typhimurium", "I 4,[5],12:i:-"},
    "Turkey": {"Hadar", "Typhimurium", "Muenchen"},
}
POULTRY_MEAT = ("Chicken", "Turkey", "Other Poultry")


def primary_serotype(s: str) -> str:
    """NORS lists one entry per aetiology; multi-serotype outbreaks are ';'-joined.

    Attribute the outbreak to its first listed serotype rather than counting it once
    per serotype, which would double-count illnesses. Composite rows are flagged so
    the report can state how much of the total they represent.
    """
    if not isinstance(s, str) or not s.strip():
        return "unspecified"
    return s.split(";")[0].strip() or "unspecified"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nors", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    N = pd.read_csv(a.nors / "nors_poultry_serotype_year.csv", dtype={"sero": "string"})
    for c in ("nb", "ill", "hosp", "dth"):
        N[c] = pd.to_numeric(N[c], errors="coerce").fillna(0).astype(int)
    N["composite"] = N["sero"].fillna("").str.contains(";")
    N["serotype"] = N["sero"].map(primary_serotype)

    res: dict = {}

    # ---- 1. Burden by serotype, poultry meat only (chicken + turkey + other poultry)
    meat = N[N["cat"].isin(POULTRY_MEAT)].copy()
    by_sero = (meat.groupby("serotype")[["nb", "ill", "hosp", "dth"]].sum()
               .sort_values("hosp", ascending=False))
    # How much of each serotype's burden comes from its single largest outbreak row?
    largest = meat.groupby("serotype")["hosp"].max()
    by_sero["largest_row_hosp"] = largest
    _denom = by_sero["hosp"].astype(float).replace(0.0, float("nan"))
    by_sero["pct_hosp_from_largest_row"] = (
        100 * by_sero["largest_row_hosp"].astype(float) / _denom
    ).round(1)
    by_sero["in_fsis_kpi"] = [s in KPI for s in by_sero.index]
    by_sero.to_csv(a.out / "t16_nors_poultry_burden_by_serotype.csv")
    res["poultry_meat_totals"] = {
        "outbreaks": int(meat["nb"].sum()), "illnesses": int(meat["ill"].sum()),
        "hospitalizations": int(meat["hosp"].sum()), "deaths": int(meat["dth"].sum()),
        "years": [int(N["year"].min()), int(N["year"].max())],
        "composite_rows": int(meat["composite"].sum()),
        "composite_hosp_pct": round(
            100 * meat.loc[meat["composite"], "hosp"].sum() / max(meat["hosp"].sum(), 1), 1),
    }
    res["top_serotypes_by_hospitalizations"] = [
        {"serotype": s, "outbreaks": int(r["nb"]), "illnesses": int(r["ill"]),
         "hospitalizations": int(r["hosp"]), "deaths": int(r["dth"]),
         "pct_hosp_from_largest_row": (None if pd.isna(r["pct_hosp_from_largest_row"])
                                       else float(r["pct_hosp_from_largest_row"])),
         "in_fsis_kpi": bool(r["in_fsis_kpi"])}
        for s, r in by_sero.head(12).iterrows()
    ]

    # ---- 2. The policy comparison, per species
    species_rows = []
    for cat, listed in FRAMEWORK_2024.items():
        sub = N[N["cat"] == cat]
        tot_h = int(sub["hosp"].sum())
        g = sub.groupby("serotype")[["nb", "ill", "hosp", "dth"]].sum()
        listed_h = int(g.reindex(sorted(listed)).fillna(0)["hosp"].sum())
        kpi_h = int(g.reindex(sorted(KPI)).fillna(0)["hosp"].sum())
        top = g.sort_values("hosp", ascending=False).head(1)
        species_rows.append({
            "species": cat,
            "total_hospitalizations": tot_h,
            "framework_2024_serotypes": sorted(listed),
            "framework_2024_hospitalizations": listed_h,
            "framework_2024_share_pct": round(100 * listed_h / tot_h, 1) if tot_h else None,
            "fsis_kpi_hospitalizations": kpi_h,
            "fsis_kpi_share_pct": round(100 * kpi_h / tot_h, 1) if tot_h else None,
            "highest_burden_serotype": top.index[0] if len(top) else None,
            "highest_burden_hospitalizations": int(top["hosp"].iloc[0]) if len(top) else None,
            "highest_burden_on_either_list": (
                bool(top.index[0] in listed or top.index[0] in KPI) if len(top) else None),
        })
    res["policy_comparison"] = species_rows

    # ---- 3. Prevalence in the supply vs burden in people (chicken)
    share = pd.read_csv(a.out / "t2b_chicken_serotype_share_routine_only.csv")
    latest_share = share.sort_values("fy").iloc[-1]
    chick = (N[N["cat"] == "Chicken"].groupby("serotype")[["nb", "hosp"]].sum())
    prev_vs_burden = []
    for s in [c for c in share.columns if c != "fy"]:
        prev_vs_burden.append({
            "serotype": s,
            "fsis_share_of_serotyped_chicken_isolates_pct_latest_fy": float(latest_share[s]),
            "fsis_share_pct_first_fy": float(share.sort_values("fy").iloc[0][s]),
            "nors_chicken_outbreaks": int(chick["nb"].get(s, 0)),
            "nors_chicken_hospitalizations": int(chick["hosp"].get(s, 0)),
            "in_fsis_kpi": s in KPI,
        })
    res["prevalence_vs_burden_chicken"] = {
        "latest_fy": int(latest_share["fy"]),
        "first_fy": int(share.sort_values("fy").iloc[0]["fy"]),
        "rows": sorted(prev_vs_burden,
                       key=lambda r: -r["fsis_share_of_serotyped_chicken_isolates_pct_latest_fy"]),
    }
    pd.DataFrame(res["prevalence_vs_burden_chicken"]["rows"]).to_csv(
        a.out / "t17_chicken_prevalence_vs_burden.csv", index=False)

    # ---- 4. How complete is food attribution at all?
    A = pd.read_csv(a.nors / "nors_salmonella_attribution.csv")
    for c in ("nb", "ill", "hosp", "dth"):
        A[c] = pd.to_numeric(A[c], errors="coerce").fillna(0).astype(int)
    A["cat"] = A["cat"].fillna("(no IFSAC category)")
    tot = int(A["hosp"].sum())
    unattr = int(A.loc[A["cat"] == "(no IFSAC category)", "hosp"].sum())
    poultry_h = int(A.loc[A["cat"].isin(POULTRY_MEAT), "hosp"].sum())
    res["attribution_completeness"] = {
        "all_salmonella_foodborne_outbreaks": int(A["nb"].sum()),
        "all_hospitalizations": tot,
        "unattributed_outbreaks": int(A.loc[A["cat"] == "(no IFSAC category)", "nb"].sum()),
        "unattributed_hospitalizations": unattr,
        "unattributed_hosp_pct": round(100 * unattr / tot, 1) if tot else None,
        "poultry_meat_hospitalizations": poultry_h,
        "poultry_meat_hosp_pct": round(100 * poultry_h / tot, 1) if tot else None,
        "note": ("Most Salmonella foodborne outbreaks carry no IFSAC food category, so "
                 "poultry-attributed burden is a floor, not an estimate of poultry's "
                 "true contribution."),
    }

    res["caveats"] = [
        "Joins are at serotype and year only. No establishment is linked to any outbreak, "
        "as the FSIS data licence requires.",
        "Outbreak-associated illness is a small, biased subset of salmonellosis; most cases "
        "are sporadic and absent from NORS.",
        "Public NORS currently ends at 2023 while FSIS sampling runs to FY2026, so the two "
        "series do not cover the same final years.",
        "Counts are small. Single large outbreaks dominate several serotypes, which is why "
        "pct_hosp_from_largest_row is reported alongside every total.",
        "NORS records can be revised after close-out, and recent years are under-reported "
        "because final data lag 12 to 18 months.",
    ]

    (a.out / "burden_weighting.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: res[k] for k in
                      ("poultry_meat_totals", "policy_comparison", "attribution_completeness")},
                     indent=1, default=str))


if __name__ == "__main__":
    main()
