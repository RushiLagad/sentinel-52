#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-27. Review it
# before relying on it.
# -----------------------------------------------------------------------------
"""Generate the SIMULATED lot inventory the decision layer acts on.

=============================================================================
EVERYTHING THIS SCRIPT PRODUCES IS SIMULATED. It is not operational data and
must never be presented as such. Every row carries is_synthetic = True, and
every figure derived from it must be labelled as simulated in the application
and in the report.
=============================================================================

Why simulate at all
-------------------
The brief asks us to convert risk predictions into decisions for a supply-chain
actor. Decisions need something to act on: lots, quantities, perishability,
destinations. A food bank's lot-level inventory is not public and cannot be
obtained in a week. The options were to skip Task 3 entirely or to
simulate the inventory from a documented procedure and say so loudly. We chose
the second.

What is real and what is not
----------------------------
REAL   establishments, their numbers, names, states, counties, product classes,
       and their actual FSIS sampling history and risk scores
REAL   Arkansas counties and their FIPS codes, SVI and food-security measures
SIM    which establishment a given lot came from, when it arrived, how much it
       weighed, its shelf life, and which county it was destined for

So every statement about RISK rests on real data. Every statement about POUNDS
rests on this simulation. The report must not blur that line.

The actor
---------
A regional food bank in Arkansas, receiving FSIS-inspected poultry and
distributing it across Arkansas counties. Arkansas because it is 9.3 percent of
all routine FSIS poultry sampling across 49 establishments, which makes the
sourcing side concrete rather than hypothetical.

Usage:
  python scripts/14_build_synthetic_inventory.py --data data/processed --out data/inventory
  python scripts/14_build_synthetic_inventory.py --data data/processed --out data/inventory \
      --vulnerability data/vulnerability/vulnerability_county.csv --seed 7
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

# Shelf life in days by product class. Frozen comminuted product keeps for
# months; fresh carcasses and parts do not. These are plausible operating
# assumptions, not measurements, and are stated as such in ASSUMPTIONS.md.
SHELF_LIFE_DAYS = {
    "chicken_carcass": 10,
    "chicken_parts": 10,
    "comminuted_chicken": 120,
    "comminuted_turkey": 120,
    "turkey_carcass": 150,
}
# Median lot weight in pounds, by product class. A lot is roughly a pallet.
MEDIAN_LOT_LB = {
    "chicken_carcass": 1400,
    "chicken_parts": 1200,
    "comminuted_chicken": 1800,
    "comminuted_turkey": 1800,
    "turkey_carcass": 1600,
}
LOT_LB_SIGMA = 0.45          # lognormal shape; gives a long right tail


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--vulnerability", type=Path, default=None,
                    help="vulnerability_county.csv, to weight destinations by need")
    ap.add_argument("--state", default="AR", help="the food bank's service state")
    ap.add_argument("--weeks", type=int, default=52)
    ap.add_argument("--lots-per-week", type=float, default=35.0)
    ap.add_argument("--suppliers-per-class", type=int, default=12,
                    help="supplier panel size per product class; stratified so every FSIS standard "
                         "is represented, not just the high-volume chicken lines")
    ap.add_argument("--end-date", default=None, help="defaults to the last sampling window")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(a.seed)

    S = pd.read_parquet(a.data / "samples.parquet",
                        columns=["establishment_id", "establishment_state", "product_class",
                                 "program", "collection_date"])
    E = pd.read_parquet(a.data / "establishments.parquet",
                        columns=["establishment_id", "establishment_number", "establishment_name",
                                 "state", "county", "fips_code", "haccp_size"])

    end = pd.Timestamp(a.end_date) if a.end_date else pd.to_datetime(S["collection_date"]).max()
    start = end - pd.Timedelta(weeks=a.weeks)

    # ---- sourcing: real establishments, weighted by recent sampling volume as a
    # stand-in for throughput. Establishments that are sampled more are, broadly,
    # producing more; FSIS does not publish production volume.
    R = S[(S["program"] == "routine") & (pd.to_datetime(S["collection_date"]) >= start - pd.Timedelta(weeks=104))]
    vol = (R.groupby(["establishment_id", "product_class"]).size()
             .rename("samples").reset_index())
    vol = vol[vol["product_class"].isin(SHELF_LIFE_DAYS)]
    vol = vol.merge(E, on="establishment_id", how="left")
    vol = vol[vol["establishment_name"].notna()]
    if vol.empty:
        raise SystemExit("no establishment/product-class pairs found; check --data")

    # A food bank has a supplier list, not the national plant population. Take the
    # highest-volume establishments **per product class**, so every FSIS standard is
    # represented. Taking the top N overall gives an almost pure chicken panel and
    # leaves the turkey standards untestable. Deterministic: volume then id.
    vol = vol.sort_values(["product_class", "samples", "establishment_id"],
                          ascending=[True, False, True])
    vol = (vol.groupby("product_class", group_keys=False)
              .head(a.suppliers_per_class).reset_index(drop=True))
    # within a class, weight by volume; across classes, give each class equal total
    # weight so the smaller lines actually appear
    vol["w"] = vol.groupby("product_class")["samples"].transform(lambda v: v / v.sum())
    vol["w"] = vol["w"] / vol["product_class"].nunique()
    w = vol["w"].to_numpy(dtype=float)
    w = w / w.sum()

    # ---- destinations: real counties in the service state
    dest = (E[E["state"] == a.state][["county", "fips_code"]]
            .dropna().drop_duplicates().reset_index(drop=True))
    used_vuln = False
    if a.vulnerability and a.vulnerability.exists():
        V = pd.read_csv(a.vulnerability, dtype={"fips": str})
        V = V[V["state"] == a.state] if "state" in V.columns else V
        dest = dest.assign(fips=dest["fips_code"].astype(str).str.extract(r"(\d{5})")[0])
        dest = dest.merge(V[["fips", "svi_overall", "population"]], on="fips", how="left")
        used_vuln = dest["svi_overall"].notna().any()
    if not used_vuln:
        # fall back: all counties in the service state, equally likely
        dest["svi_overall"] = 0.5
        dest["population"] = 1.0
    # A food bank distributes toward need: weight by population and by vulnerability.
    dw = (pd.to_numeric(dest["population"], errors="coerce").fillna(1.0).clip(lower=1.0)
          * (0.5 + pd.to_numeric(dest["svi_overall"], errors="coerce").fillna(0.5))).to_numpy()
    dw = dw / dw.sum()

    # ---- lots
    n_weeks = a.weeks
    per_week = rng.poisson(a.lots_per_week, size=n_weeks)
    rows, lot_no = [], 0
    for wk in range(n_weeks):
        week_start = start + pd.Timedelta(weeks=wk)
        for _ in range(int(per_week[wk])):
            i = rng.choice(len(vol), p=w)
            src = vol.iloc[i]
            pc = src["product_class"]
            d = rng.choice(len(dest), p=dw)
            dst = dest.iloc[d]
            received = week_start + pd.Timedelta(days=int(rng.integers(0, 7)))
            shelf = SHELF_LIFE_DAYS[pc]
            # shelf life varies a little around the nominal value
            shelf_actual = max(2, int(round(shelf * float(rng.normal(1.0, 0.12)))))
            pounds = float(np.exp(rng.normal(np.log(MEDIAN_LOT_LB[pc]), LOT_LB_SIGMA)))
            lot_no += 1
            rows.append({
                "lot_id": f"SIM-{a.seed}-{lot_no:06d}",
                "is_synthetic": True,
                "establishment_id": src["establishment_id"],
                "establishment_number": src["establishment_number"],
                "establishment_name": src["establishment_name"],
                "source_state": src["state"],
                "source_county": src["county"],
                "haccp_size": src["haccp_size"],
                "product_class": pc,
                "received_date": received.date().isoformat(),
                "use_by_date": (received + pd.Timedelta(days=shelf_actual)).date().isoformat(),
                "shelf_life_days": shelf_actual,
                "pounds": round(pounds, 1),
                "dest_county": dst["county"],
                "dest_fips": dst.get("fips", dst["fips_code"]),
                "dest_svi_overall": (None if pd.isna(dst["svi_overall"]) else float(dst["svi_overall"])),
            })

    L = pd.DataFrame(rows)
    L.to_csv(a.out / "lots_synthetic.csv", index=False)

    assumptions = {
        "WARNING": "SIMULATED DATA. Not operational. Every row has is_synthetic = True.",
        "seed": a.seed,
        "deterministic": "same seed and same input data reproduce this file exactly",
        "actor": f"regional food bank serving {a.state}",
        "window": [start.date().isoformat(), end.date().isoformat()],
        "lots": int(len(L)),
        "total_pounds": round(float(L["pounds"].sum()), 1),
        "establishments_sourced_from": int(L["establishment_id"].nunique()),
        "supplier_panel_size": int(len(vol["establishment_id"].unique())),
        "suppliers_per_class": a.suppliers_per_class,
        "median_lots_per_supplier": float(L.groupby("establishment_id").size().median()),
        "destination_counties": int(L["dest_county"].nunique()),
        "destinations_weighted_by_vulnerability": bool(used_vuln),
        "real_components": [
            "establishment identity, name, number, state, county, HACCP size",
            "product classes, matching the FSIS standards",
            f"{a.state} counties and their FIPS codes",
            "SVI and population, where the vulnerability file was supplied",
        ],
        "simulated_components": [
            "which establishment each lot came from",
            "arrival dates and arrival rate",
            "lot weights",
            "shelf life",
            "destination county for each lot",
        ],
        "parameters": {
            "lots_per_week_mean": a.lots_per_week,
            "arrival_process": "Poisson per week, uniform day within the week",
            "lot_weight": "lognormal, median by product class, sigma 0.45",
            "median_lot_lb": MEDIAN_LOT_LB,
            "shelf_life_days_nominal": SHELF_LIFE_DAYS,
            "shelf_life_variation": "normal, mean 1.0, sd 0.12 of nominal, floor 2 days",
            "sourcing_weight": "recent routine sampling volume per establishment and product class, "
                               "used as a proxy for throughput because FSIS does not publish "
                               "production volume",
            "destination_weight": "county population times (0.5 + SVI overall percentile)",
        },
        "known_distortions": [
            "Sampling volume is an imperfect proxy for throughput. FSIS samples by risk and by "
            "programme, not in proportion to production, so high-sampled plants are over-represented.",
            "The supplier panel takes the highest-volume establishments in each product class, so "
            "it over-represents large plants. Category 3 concentrates in very small plants (25.4 "
            "percent against 6.7 percent for large), so this panel understates how often a real "
            "food bank would face a high-risk source.",
            "Product classes are given equal total weight so that the turkey standards appear at "
            "all. Real poultry volume is overwhelmingly chicken, so the product mix here is "
            "deliberately unrepresentative, in exchange for exercising every standard.",
            "A real food bank receives most product through distributors and retail rescue, not "
            "directly from slaughter establishments. Direct sourcing is a simplification that makes "
            "the establishment-to-lot link tractable.",
            "Lot weights and shelf lives are plausible operating values, not measurements.",
            "Destination weighting assumes a food bank distributes toward need. Real allocation is "
            "constrained by agency networks, storage and transport, none of which are modelled.",
        ],
    }
    (a.out / "ASSUMPTIONS.json").write_text(json.dumps(assumptions, indent=1, default=str))
    print(json.dumps({k: assumptions[k] for k in
                      ("lots", "total_pounds", "establishments_sourced_from",
                       "median_lots_per_supplier", "destination_counties",
                       "destinations_weighted_by_vulnerability")}, indent=1))
    print(f"\nwrote {a.out/'lots_synthetic.csv'}  (SIMULATED)")


if __name__ == "__main__":
    main()
