#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-31 by Sambhavi
# Patel; mark join corrected on review 2026-11-01. Run against the real panel.
# -----------------------------------------------------------------------------
"""Marginal value of the team-added datasets in the risk model (Task 2 / Task 5).

05d ablates FSIS feature families. The brief asks for the marginal value of the
data the team *added*. This script adds two groups built from the added layers and
runs the same leave-one-group-out comparison on the same time-aware split:

  noaa_climate   state-level TAVG/TMAX/PRCP for the plant's state, trailing 3 months
                 as of the window end, plus a TAVG anomaly against a climatology fit
                 on TRAINING month-ends only (no test-period information leaks in).
  fsis_recalls   linked poultry/Salmonella recalls for the plant's mark in the 24
                 months up to the window end (strictly dated <= window_end).

SVI is not ablated here: it is county-of-destination, not a property of the
plant, so it belongs to the decision layer (see 16), not the risk model.

Outputs t19b_added_data_ablation_h{H}.csv and ablation_added_h{H}.json. Does not
touch 05d's outputs, so the byte-identical h6 results stay as they are.

Usage:
  python scripts/05e_added_data_ablation.py --data ../data/processed --raw-data ../data \
      --out outputs --horizon 6
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from importlib import import_module

_abl = import_module("05d_ablation")  # reuse GROUPS, fit_score, boot_delta unchanged
GROUPS, fit_score, boot_delta = _abl.GROUPS, _abl.fit_score, _abl.boot_delta

CLIMATE = ["tavg_3m", "tmax_3m", "prcp_3m", "tavg_anom_3m"]
RECALL = ["recalls_24m", "any_recall_24m"]


def norm_mark(s: str) -> str:
    # "P-20935A", "P20935 A", "p20935a" -> "P20935A"
    return re.sub(r"[^A-Z0-9]", "", str(s).upper())


def mark_table(est: pd.DataFrame) -> pd.DataFrame:
    """One row per (mark, establishment_id).

    The directory stores a plant's grants joined with '+', as in 'M795B+P795B',
    so a plant has one row per grant here. A recall notice sometimes gives only
    the number without the letter ('18004' for 'P18004'); those bare numbers
    are matched on the number alone. Marks or numbers that resolve to more
    than one establishment are left out rather than guessed. Reviewed and
    corrected 2026-11-01: the first version joined on the whole '+' string and
    linked two notices instead of the hundred or so that resolve.
    """
    m = est[["establishment_id", "establishment_number"]].dropna().copy()
    m = m.assign(mark=m["establishment_number"].astype(str).str.split("+")).explode("mark")
    m["mark"] = m["mark"].map(norm_mark)
    m = m[m["mark"] != ""].drop_duplicates(["mark", "establishment_id"])
    amb = m.groupby("mark")["establishment_id"].nunique()
    m = m[m["mark"].isin(amb[amb == 1].index)]
    m["number"] = m["mark"].str.replace(r"^[A-Z]+", "", regex=True)
    return m[["mark", "number", "establishment_id"]]


def add_climate(D: pd.DataFrame, noaa: pd.DataFrame, train_cut: pd.Timestamp) -> pd.DataFrame:
    n = noaa.copy()
    n["ym"] = pd.PeriodIndex(n["date"], freq="M")
    n = n.sort_values(["state", "ym"])
    for v, out in (("TAVG", "tavg_3m"), ("TMAX", "tmax_3m"), ("PRCP", "prcp_3m")):
        # trailing 3 months ending at the window-end month; min_periods avoids silent zeros
        n[out] = n.groupby("state")[v].transform(lambda s: s.rolling(3, min_periods=2).mean())
    # climatology from training-period months only
    clim = (n[n["ym"].dt.to_timestamp(how="end") <= train_cut]
            .groupby(["state", n["ym"].dt.month])["tavg_3m"].mean()
            .rename("tavg_clim").reset_index().rename(columns={"ym": "cal_month"}))
    n["cal_month"] = n["ym"].dt.month
    n = n.merge(clim, on=["state", "cal_month"], how="left")
    n["tavg_anom_3m"] = n["tavg_3m"] - n["tavg_clim"]
    D = D.copy()
    D["ym"] = D["window_end"].dt.to_period("M")
    before = len(D)
    D = D.merge(n[["state", "ym"] + CLIMATE], on=["state", "ym"], how="left")
    assert len(D) == before, "climate join duplicated rows: noaa_state_month not unique per state-month"
    return D.drop(columns="ym")


def add_recalls(D: pd.DataFrame, rec: pd.DataFrame, est: pd.DataFrame) -> pd.DataFrame:
    rec = rec[rec["est_marks"].notna() & (rec["est_marks"].astype(str) != "")].copy()
    rec["recall_date"] = pd.to_datetime(rec["recall_date"], errors="coerce")
    n_marked = rec["recall_number"].nunique()
    rec = rec.assign(mark=rec["est_marks"].astype(str).str.split("|")).explode("mark")
    rec["mark"] = rec["mark"].map(norm_mark)
    m = mark_table(est)
    by_mark = m.drop_duplicates("mark")[["mark", "establishment_id"]]
    by_num = m.groupby("number")["establishment_id"].agg(lambda x: x.iloc[0] if x.nunique() == 1 else None)
    by_num = by_num.dropna().astype(int).rename("establishment_id").reset_index()
    has_letter = rec["mark"].str.match(r"^[A-Z]")
    rec_l = rec[has_letter].merge(by_mark, on="mark", how="inner")
    rec_n = rec[~has_letter].rename(columns={"mark": "number"}).merge(by_num, on="number", how="inner")
    rec = pd.concat([rec_l, rec_n], ignore_index=True)
    rl = rec[["establishment_id", "recall_date", "recall_number"]].drop_duplicates()
    print(f"  recalls: {n_marked} notices with a mark, "
          f"{rl['recall_number'].nunique()} linked to {rl['establishment_id'].nunique()} establishments")
    rl = rl[["establishment_id", "recall_date"]]
    D = D.copy()
    keys = D[["establishment_id", "window_end"]].drop_duplicates()
    j = keys.merge(rl, on="establishment_id", how="left")
    lo = j["window_end"] - pd.DateOffset(months=24)
    j["hit"] = (j["recall_date"] > lo) & (j["recall_date"] <= j["window_end"])  # strictly as-of
    cnt = j.groupby(["establishment_id", "window_end"])["hit"].sum().rename("recalls_24m").reset_index()
    D = D.merge(cnt, on=["establishment_id", "window_end"], how="left")
    D["recalls_24m"] = D["recalls_24m"].fillna(0).astype(float)
    D["any_recall_24m"] = (D["recalls_24m"] > 0).astype(float)
    return D


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True, help="data/processed")
    ap.add_argument("--raw-data", type=Path, required=True, help="data/ (noaa/, fsis_recalls/)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--horizon", type=int, default=6)
    ap.add_argument("--train-end", default="2022-12-31")
    ap.add_argument("--test-start", default="2024-01-01")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--bootstrap", type=int, default=300)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    H = a.horizon

    P = pd.read_parquet(a.data / f"panel_monthly_h{H}.parquet")
    D = P[P["category"].isin(["1", "2"]) & P["horizon_complete"] & P["rated_in_horizon"]].copy()
    train_cut = pd.Timestamp(a.train_end) - pd.DateOffset(months=H)

    D = add_climate(D, pd.read_csv(a.raw_data / "noaa" / "noaa_state_month.csv"), train_cut)
    D = add_recalls(D, pd.read_csv(a.raw_data / "fsis_recalls" / "fsis_recalls_poultry_salmonella.csv"),
                    pd.read_parquet(a.data / "establishments.parquet"))

    groups_all = {**GROUPS, "noaa_climate": CLIMATE, "fsis_recalls": RECALL}
    tr = D[D["window_end"] <= train_cut]
    te = D[D["window_end"] >= a.test_start]
    feats = [f for g in groups_all.values() for f in g]
    dead = [f for f in feats if tr[f].notna().sum() == 0 or tr[f].nunique(dropna=True) <= 1]
    feats = [f for f in feats if f not in dead]
    groups = {g: [f for f in fs if f in feats] for g, fs in groups_all.items()}
    cov = {f: round(float(D[f].notna().mean()), 4) for f in CLIMATE + RECALL}
    print(f"  coverage of added features: {cov}\n  dropped (no signal in training): {dead}")

    ytr, yte = tr["y"].to_numpy(), te["y"].to_numpy()
    est = te["establishment_id"].to_numpy()
    base = [f for f in feats if f not in CLIMATE + RECALL]   # = 05d's full model
    s_base = fit_score(tr[base], ytr, te[base], a.seed)
    s_full = fit_score(tr[feats], ytr, te[feats], a.seed)

    rows = []
    # (a) ADD each layer to the 05d model; (b) DROP each layer from the model that has both
    for name, keep in [("add_noaa_climate", base + groups["noaa_climate"]),
                       ("add_fsis_recalls", base + groups["fsis_recalls"]),
                       ("add_both", feats)]:
        if keep == base:
            # layer had no variation in training (e.g. linked recalls all post-train_cut)
            rows.append({"comparison": name, "reference": "05d_full_model",
                         "verdict": "not testable: no signal in training period"})
            print(f"  {name:<18} not testable: no signal in training period")
            continue
        s = s_full if name == "add_both" else fit_score(tr[keep], ytr, te[keep], a.seed)
        d_auc, d_ap = boot_delta(yte, s_base, s, est, a.bootstrap, a.seed)  # s - base
        rows.append({"comparison": name, "reference": "05d_full_model",
                     "auroc": round(float(roc_auc_score(yte, s)), 4),
                     "d_auroc": round(float(roc_auc_score(yte, s) - roc_auc_score(yte, s_base)), 4),
                     "d_auroc_lo": d_auc["lo"], "d_auroc_hi": d_auc["hi"],
                     "avg_precision": round(float(average_precision_score(yte, s)), 4),
                     "d_avg_precision": round(float(average_precision_score(yte, s)
                                                    - average_precision_score(yte, s_base)), 4),
                     "d_ap_lo": d_ap["lo"], "d_ap_hi": d_ap["hi"],
                     "distinguishable_from_zero": not (d_auc["lo"] <= 0 <= d_auc["hi"])})
        print(f"  {name:<18} AUROC {rows[-1]['auroc']:.4f} ({rows[-1]['d_auroc']:+.4f}, "
              f"CI {d_auc['lo']:+.4f}..{d_auc['hi']:+.4f})")

    pd.DataFrame(rows).to_csv(a.out / f"t19b_added_data_ablation_h{H}.csv", index=False)
    (a.out / f"ablation_added_h{H}.json").write_text(json.dumps(
        {"horizon_months": H, "seed": a.seed, "bootstrap_resamples": a.bootstrap,
         "train_cut": str(train_cut.date()), "test_start": a.test_start,
         "added_feature_coverage": cov, "dropped_no_signal": dead,
         "base_auroc": round(float(roc_auc_score(yte, s_base)), 4), "rows": rows}, indent=1))
    print(f"wrote {a.out / f't19b_added_data_ablation_h{H}.csv'}")


if __name__ == "__main__":
    main()
