#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-26. Review it
# before relying on it.
# -----------------------------------------------------------------------------
"""Marginal value of each data source: leave-one-group-out ablation.

The brief (Task 2) asks for "the marginal value of added data", and Task 5 asks
for an ablation showing the effect of the data we added. This answers both by
dropping one source group at a time from the integrated model and measuring what
is lost, on the same time-aware split as 05.

Groups map to parts of the data product, not to arbitrary feature bundles, so a
row of this table answers "was it worth pulling this in?". New sources
(NOAA climate, FSIS recalls, SVI, food access) slot into GROUPS when they land
and the table extends without changing anything else.

Honesty notes built in:
  * Deltas are reported with establishment-clustered bootstrap intervals, because
    consecutive month-end rows for one plant are not independent.
  * A group whose interval straddles zero is reported as such and stays in the
    table. A source that did not help is a finding, not something to delete.
  * `fsis_core_only` shows what everything beyond basic sampling history buys in
    aggregate, which is the number the report should quote rather than a sum of
    the individual deltas.

Usage:
  python scripts/05d_ablation.py --data data/processed --out outputs --horizon 6
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

from fsis_categories import STANDARDS

CLASSES = list(STANDARDS)

# Feature groups, each standing for a distinct part of the data we pull in.
GROUPS: dict[str, list[str]] = {
    "sampling_history": ["n52", "pos52", "rate52", "n13", "pos13", "rate13", "n26", "pos26",
                         "rate26", "trend13", "rate_prev", "rate_all", "class_rate52"],
    "standard_position": ["spare3", "spare3_frac", "is_cat2", "months_cat3_prev24"],
    "projection": ["projection_logit"],
    "serotype_detail": ["share_infantis", "share_enteritidis", "share_typhimurium", "share_kentucky"],
    "enumeration_cfu": ["cfu_ge10_share"],
    "other_pathogens": ["campy_rate52", "other_rate52"],
    "followup_program": ["in_followup", "followup_n52"],
    "establishment_profile": ["size_small", "size_very_small", "npis",
                              "slaughter_volume_category", "processing_volume_category"],
    "seasonality": ["month"],
    "product_class": [f"cls_{c}" for c in CLASSES],
}
# Everything outside these two groups is "added" relative to basic FSIS sampling.
CORE = ["sampling_history", "standard_position"]


def fit_score(Xtr, ytr, Xte, seed: int):
    m = HistGradientBoostingClassifier(max_depth=4, learning_rate=0.06, max_iter=400,
                                       l2_regularization=1.0, random_state=seed)
    m.fit(Xtr, ytr)
    return m.predict_proba(Xte)[:, 1]


def boot_delta(y, s_full, s_drop, groups, n: int, seed: int):
    """Bootstrap the *paired* delta in AUROC and AP, resampling whole establishments."""
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    idx_by = {g: np.flatnonzero(groups == g) for g in uniq}
    d_auc, d_ap = [], []
    for _ in range(n):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([idx_by[g] for g in pick])
        yy = y[idx]
        if yy.min() == yy.max():
            continue
        d_auc.append(roc_auc_score(yy, s_drop[idx]) - roc_auc_score(yy, s_full[idx]))
        d_ap.append(average_precision_score(yy, s_drop[idx]) - average_precision_score(yy, s_full[idx]))
    q = lambda v: {"lo": round(float(np.percentile(v, 2.5)), 4),
                   "median": round(float(np.percentile(v, 50)), 4),
                   "hi": round(float(np.percentile(v, 97.5)), 4)}
    return q(d_auc), q(d_ap)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
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
    tr = D[D["window_end"] <= train_cut]
    te = D[D["window_end"] >= a.test_start]

    feats = [f for g in GROUPS.values() for f in g]
    missing = [f for f in feats if f not in D.columns]
    if missing:
        raise SystemExit(f"panel is missing expected features: {missing}")
    # match 05: drop anything with no signal in training
    dead = [f for f in feats if tr[f].notna().sum() == 0 or tr[f].nunique(dropna=True) <= 1]
    feats = [f for f in feats if f not in dead]
    groups = {g: [f for f in fs if f in feats] for g, fs in GROUPS.items()}

    ytr, yte = tr["y"].to_numpy(), te["y"].to_numpy()
    est = te["establishment_id"].to_numpy()

    s_full = fit_score(tr[feats], ytr, te[feats], a.seed)
    auc_full = roc_auc_score(yte, s_full)
    ap_full = average_precision_score(yte, s_full)

    res: dict = {
        "horizon_months": H,
        "train_rows": int(len(tr)), "test_rows": int(len(te)),
        "test_establishments": int(len(np.unique(est))),
        "test_base_rate": round(float(yte.mean()), 4),
        "features_used": len(feats),
        "features_dropped_no_signal_in_training": dead,
        "full_model": {"auroc": round(float(auc_full), 4), "avg_precision": round(float(ap_full), 4)},
        "bootstrap_resamples": a.bootstrap,
        "ablations": [],
    }

    runs = [(g, [f for f in feats if f not in fs]) for g, fs in groups.items() if fs]
    core_feats = [f for g in CORE for f in groups.get(g, [])]
    runs.append(("ALL_beyond_fsis_core", core_feats))

    for name, keep in runs:
        if not keep:
            continue
        s = fit_score(tr[keep], ytr, te[keep], a.seed)
        auc, apr = roc_auc_score(yte, s), average_precision_score(yte, s)
        d_auc, d_ap = boot_delta(yte, s_full, s, est, a.bootstrap, a.seed)
        row = {
            "dropped": name,
            "n_features_dropped": len(feats) - len(keep),
            "auroc": round(float(auc), 4), "d_auroc": round(float(auc - auc_full), 4),
            "d_auroc_ci": d_auc,
            "avg_precision": round(float(apr), 4), "d_avg_precision": round(float(apr - ap_full), 4),
            "d_avg_precision_ci": d_ap,
            # the interval straddling zero is the honest read, not a p-value
            "auroc_change_distinguishable_from_zero": not (d_auc["lo"] <= 0 <= d_auc["hi"]),
        }
        res["ablations"].append(row)
        print(f"  drop {name:<24} AUROC {auc:.4f} ({auc-auc_full:+.4f})  "
              f"AP {apr:.4f} ({apr-ap_full:+.4f})  "
              f"{'distinguishable' if row['auroc_change_distinguishable_from_zero'] else 'within noise'}")

    tab = pd.DataFrame([{k: r[k] for k in ("dropped", "n_features_dropped", "auroc", "d_auroc",
                                           "avg_precision", "d_avg_precision",
                                           "auroc_change_distinguishable_from_zero")}
                        for r in res["ablations"]])
    tab["d_auroc_lo"] = [r["d_auroc_ci"]["lo"] for r in res["ablations"]]
    tab["d_auroc_hi"] = [r["d_auroc_ci"]["hi"] for r in res["ablations"]]
    tab.sort_values("d_auroc").to_csv(a.out / f"t19_ablation_h{H}.csv", index=False)
    (a.out / f"ablation_h{H}.json").write_text(json.dumps(res, indent=1))
    print(f"\nFull model AUROC {auc_full:.4f}, AP {ap_full:.4f}")
    print(f"wrote {a.out / f'ablation_h{H}.json'}")


if __name__ == "__main__":
    main()
