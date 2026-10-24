#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-09 and run end to
# end on the real FSIS files. Review it before relying on it.
# -----------------------------------------------------------------------------
"""First-look early-warning baseline: which establishments are about to fail?

Unit        establishment x product class, observed at each month-end window
            (52 Sunday-to-Saturday weeks ending on the last Saturday of a month)
Question    among units that are currently Category 1 or 2, which will be
            Category 3 at any month-end in the next H months?
Scorers     (a) "currently Category 2" flag
            (b) positives to spare before the Category 3 line
            (c) binomial projection: carry the positives that stay in the window
                forward and project new ones at the unit's own smoothed rate
            (d) logistic regression and (e) gradient boosting on window features
Split       strictly by time. Train on month-ends through mid-2022, test on
            2024-2025. No row's outcome window overlaps the test period.

Why the baselines matter: consecutive 52-week windows share most of their
samples, so a lot of "prediction" is arithmetic. A model only earns its place
if it beats (b) and (c).

Usage:
  python scripts/05_early_warning_baseline.py --data data/processed --out outputs --horizon 6
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from fsis_categories import STANDARDS, VACCINE_EXCLUSION_FROM, allowed_positives, categorize, last_saturday_of_month

CLASSES = list(STANDARDS)
SEROS = ["Infantis", "Enteritidis", "Typhimurium", "Kentucky"]
WEEK0 = pd.Timestamp("2013-10-05")  # first Saturday of FY2014


def week_index(d: pd.Series) -> np.ndarray:
    """Index of the Sunday-to-Saturday week a date falls in (0 = week ending 2013-10-05)."""
    week_end = d + pd.to_timedelta((5 - d.dt.dayofweek) % 7, unit="D")
    return ((week_end - WEEK0).dt.days // 7).to_numpy()


def roll(cum: np.ndarray, w: int, k: int) -> np.ndarray:
    """Sum over the k weeks ending at week w, from a cumulative-sum matrix (units x weeks)."""
    lo = w - k
    return cum[:, w] - (cum[:, lo] if lo >= 0 else 0)


def build_panel(S: pd.DataFrame, I: pd.DataFrame, E: pd.DataFrame, horizon: int) -> pd.DataFrame:
    S = S[S["product_class"].isin(CLASSES) & S["collection_date"].notna()].copy()
    S["w"] = week_index(S["collection_date"])
    R = S[(S["program"] == "routine") & S["sal_result"].notna()].copy()
    units = R.groupby(["establishment_id", "product_class"], observed=True).size().reset_index()[["establishment_id", "product_class"]]
    units["u"] = np.arange(len(units))
    n_w = int(S["w"].max()) + 1
    key = units.set_index(["establishment_id", "product_class"])["u"]

    def mat(df: pd.DataFrame, value: str | None) -> np.ndarray:
        d = df.merge(units, on=["establishment_id", "product_class"], how="inner")
        m = np.zeros((len(units), n_w), dtype=np.float32)
        v = np.ones(len(d), dtype=np.float32) if value is None else d[value].astype(float).to_numpy(dtype=np.float32)
        np.add.at(m, (d["u"].to_numpy(), d["w"].to_numpy()), v)
        return m.cumsum(axis=1)

    cN = mat(R, None); cP_all = mat(R, "sal_result"); cP_cat = mat(R, "sal_result_cat")
    Cy = R[R["campy_result"].notna()]; cCN = mat(Cy, None); cCP = mat(Cy, "campy_result")
    F = S[(S["program"] == "followup") & S["sal_result"].notna()]; cFN = mat(F, None); cFP = mat(F, "sal_result")
    iso = I[I["program"].eq("routine") & I["serotype_clean"].notna() & ~I["vaccine_strain"]].merge(R[["form_id", "w"]].drop_duplicates("form_id"), on="form_id")
    cSero = {s: mat(iso[iso["serotype_clean"] == s], None) for s in SEROS}; cSeroAll = mat(iso, None)
    cfu = R[R["sal_cfu_sign"].notna()].copy(); cfu["ge10"] = cfu["sal_cfu_ge10"].astype(float); cQN = mat(cfu, None); cQ10 = mat(cfu, "ge10")

    ends = [last_saturday_of_month(y, m) for y in range(2016, 2027) for m in range(1, 13)]
    last_w = int(R["w"].max())
    ends = [e for e in ends if e >= pd.Timestamp("2016-06-01") and (e - WEEK0).days // 7 <= last_w]
    cls_arr = units["product_class"].to_numpy()
    frames, cats = [], {}
    for e in ends:
        w = (e - WEEK0).days // 7
        cP = cP_cat if e >= VACCINE_EXCLUSION_FROM else cP_all
        n52, p52 = roll(cN, w, 52), roll(cP, w, 52)
        cat = np.full(len(units), "NA", dtype=object)
        a1 = np.zeros(len(units)); a3 = np.zeros(len(units))
        for c in CLASSES:
            m = cls_arr == c
            cat[m] = categorize(n52[m], p52[m], c)
            x1, x3 = allowed_positives(n52[m], c); a1[m], a3[m] = x1, x3
        cats[e] = cat
        f = pd.DataFrame({"u": units["u"], "window_end": e, "category": cat, "n52": n52, "pos52": p52,
                          "allowed3": a3, "allowed1": a1,
                          "n13": roll(cN, w, 13), "pos13": roll(cP, w, 13), "n26": roll(cN, w, 26), "pos26": roll(cP, w, 26),
                          "n52_prev": roll(cN, w - 52, 52) if w >= 104 else np.nan, "pos52_prev": roll(cP, w - 52, 52) if w >= 104 else np.nan,
                          "n_all": cN[:, w], "pos_all": cP_all[:, w],
                          "campy_n52": roll(cCN, w, 52), "campy_pos52": roll(cCP, w, 52),
                          "followup_n52": roll(cFN, w, 52), "followup_pos52": roll(cFP, w, 52),
                          "sero_n52": roll(cSeroAll, w, 52), "cfu_n52": roll(cQN, w, 52), "cfu_ge10_52": roll(cQ10, w, 52)})
        for s in SEROS:
            f[f"sero_{s.lower()}_52"] = roll(cSero[s], w, 52)
        # pieces needed for the binomial projection at each lead h (months)
        for h in range(1, horizon + 1):
            k = int(round(h * 52 / 12))
            f[f"n_keep_{h}"] = roll(cN, w, 52 - k); f[f"pos_keep_{h}"] = roll(cP, w, 52 - k); f[f"n_recent_{h}"] = roll(cN, w, k)
        frames.append(f)
    P = pd.concat(frames, ignore_index=True).merge(units, on="u")

    # outcome: Category 3 at any of the next H month-ends, and whether the unit was still being sampled
    idx = {e: i for i, e in enumerate(ends)}
    cat_mat = np.stack([cats[e] for e in ends], axis=1)                       # units x month-ends
    is3 = (cat_mat == "3"); rated = (cat_mat != "NA")
    fut3 = np.zeros_like(is3, dtype=bool); futr = np.zeros_like(is3, dtype=bool); complete = np.zeros(len(ends), dtype=bool)
    for i in range(len(ends)):
        j = min(i + horizon, len(ends) - 1)
        if i + horizon <= len(ends) - 1:
            complete[i] = True
        fut3[:, i] = is3[:, i + 1:j + 1].any(axis=1) if j > i else False
        futr[:, i] = rated[:, i + 1:j + 1].any(axis=1) if j > i else False
    hist3 = np.zeros(is3.shape, dtype=np.float32)                              # months in Category 3 during the previous 24 month-ends
    for i in range(len(ends)):
        hist3[:, i] = is3[:, max(0, i - 24):i].sum(axis=1)
    ei = P["window_end"].map(idx).to_numpy(); ui = P["u"].to_numpy()
    P["y"] = fut3[ui, ei].astype(int); P["rated_in_horizon"] = futr[ui, ei]; P["horizon_complete"] = complete[ei]
    P["months_cat3_prev24"] = hist3[ui, ei]

    # same establishment, other product classes
    tot = P.groupby(["establishment_id", "window_end"])[["n52", "pos52"]].transform("sum")
    P["other_n52"] = tot["n52"] - P["n52"]; P["other_pos52"] = tot["pos52"] - P["pos52"]
    # pooled product-class rate known at the window end (prior for shrinkage)
    cls_tot = P.groupby(["product_class", "window_end"])[["n52", "pos52"]].transform("sum")
    P["class_rate52"] = cls_tot["pos52"] / cls_tot["n52"].replace(0, np.nan)

    P = P.merge(E[["establishment_id", "haccp_size", "slaughter_volume_category", "processing_volume_category", "inspection_system_npis", "state", "company_key"]], on="establishment_id", how="left")
    return P


def add_features(P: pd.DataFrame, horizon: int, prior_strength: float = 20.0) -> tuple[pd.DataFrame, list[str]]:
    P = P.copy()
    div = lambda a, b: a / b.replace(0, np.nan)
    P["rate52"] = div(P["pos52"], P["n52"]); P["rate13"] = div(P["pos13"], P["n13"]); P["rate26"] = div(P["pos26"], P["n26"])
    P["rate_prev"] = div(P["pos52_prev"], P["n52_prev"]); P["rate_all"] = div(P["pos_all"], P["n_all"])
    P["trend13"] = P["rate13"] - P["rate52"]
    P["spare3"] = P["allowed3"] - P["pos52"]                                   # positives to spare before Category 3
    P["spare3_frac"] = P["spare3"] / (P["allowed3"] + 1)
    P["is_cat2"] = (P["category"] == "2").astype(int)
    P["campy_rate52"] = div(P["campy_pos52"], P["campy_n52"]); P["other_rate52"] = div(P["other_pos52"], P["other_n52"])
    P["in_followup"] = (P["followup_n52"] > 0).astype(int)
    for s in SEROS:
        P[f"share_{s.lower()}"] = div(P[f"sero_{s.lower()}_52"], P["sero_n52"])
    P["cfu_ge10_share"] = div(P["cfu_ge10_52"], P["cfu_n52"])
    P["size_small"] = (P["haccp_size"] == "Small").astype(float); P["size_very_small"] = (P["haccp_size"] == "Very Small").astype(float)
    P["npis"] = P["inspection_system_npis"].fillna(False).astype(float)
    P["month"] = P["window_end"].dt.month
    for c in CLASSES:
        P[f"cls_{c}"] = (P["product_class"] == c).astype(float)
    # binomial projection: P(Category 3 at lead h) = P(new positives > allowed - kept positives), then the max over leads
    p_hat = ((P["pos52"] + prior_strength * P["class_rate52"]) / (P["n52"] + prior_strength)).clip(1e-4, 0.999)
    proj = np.zeros(len(P))
    for h in range(1, horizon + 1):
        n_new = P[f"n_recent_{h}"].round().to_numpy(); n_fut = P[f"n_keep_{h}"].to_numpy() + n_new
        allowed = np.zeros(len(P))
        for c in CLASSES:
            m = (P["product_class"] == c).to_numpy()
            allowed[m] = allowed_positives(n_fut[m], c)[1]
        need = allowed - P[f"pos_keep_{h}"].to_numpy()                          # new positives the unit can still absorb
        ph = binom.sf(need, n_new, p_hat.to_numpy())                            # P(X > need)
        ph = np.where(n_new <= 0, (need < 0).astype(float), ph)
        proj = np.maximum(proj, ph)
    P["projection"] = proj
    P["projection_logit"] = np.log((proj + 1e-4) / (1 - proj + 1e-4))
    feats = ["n52", "pos52", "rate52", "n13", "pos13", "rate13", "n26", "pos26", "rate26", "trend13", "rate_prev", "rate_all", "spare3", "spare3_frac",
             "is_cat2", "months_cat3_prev24", "campy_rate52", "other_rate52", "in_followup", "followup_n52", "share_infantis", "share_enteritidis",
             "share_typhimurium", "share_kentucky", "cfu_ge10_share", "size_small", "size_very_small", "npis", "slaughter_volume_category",
             "processing_volume_category", "month", "class_rate52", "projection_logit"] + [f"cls_{c}" for c in CLASSES]
    return P, feats


def top_share_metrics(y: np.ndarray, score: np.ndarray, groups: np.ndarray, share: float = 0.10) -> tuple[float, float]:
    """Flag the top `share` of units by score within each month; return (recall, precision) pooled over months."""
    df = pd.DataFrame({"y": y, "s": score, "g": groups})
    df["rk"] = df.groupby("g")["s"].rank(method="first", ascending=False)
    df["k"] = np.ceil(df.groupby("g")["s"].transform("size") * share)
    flagged = df["rk"] <= df["k"]
    return float(df.loc[flagged, "y"].sum() / max(df["y"].sum(), 1)), float(df.loc[flagged, "y"].mean())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--horizon", type=int, default=6); ap.add_argument("--train-end", default="2022-12-31")
    ap.add_argument("--test-start", default="2024-01-01"); ap.add_argument("--seed", type=int, default=7); ap.add_argument("--bootstrap", type=int, default=300)
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    S = pd.read_parquet(a.data / "samples.parquet"); I = pd.read_parquet(a.data / "sal_isolates.parquet"); E = pd.read_parquet(a.data / "establishments.parquet")
    H = a.horizon
    P = build_panel(S, I, E, H); P, feats = add_features(P, H)
    P.to_parquet(a.data / f"panel_monthly_h{H}.parquet", index=False)

    res: dict = {"horizon_months": H, "panel_rows": int(len(P)), "units": int(P["u"].nunique()), "month_ends": int(P["window_end"].nunique()),
                 "first_window_end": str(P["window_end"].min().date()), "last_window_end": str(P["window_end"].max().date())}

    # how sticky are categories? where units rated today sit H months later (test period)
    idx = P.set_index(["u", "window_end"])["category"]
    ends = sorted(P["window_end"].unique()); nxt = {e: ends[i + H] for i, e in enumerate(ends) if i + H < len(ends)}
    T = P[P["window_end"].isin(nxt) & (P["window_end"] >= a.test_start) & (P["category"] != "NA")].copy()
    T["cat_later"] = [idx.get((u, nxt[e]), "NA") for u, e in zip(T["u"], T["window_end"])]
    trans = pd.crosstab(T["category"], T["cat_later"], normalize="index").mul(100).round(1)
    print(f"\nWhere a unit sits {H} months later, by category today (% of row), window ends from {a.test_start}:\n", trans.to_string())
    res["transition_pct"] = {str(k): {str(c): float(v) for c, v in row.items()} for k, row in trans.iterrows()}

    # early-warning task: currently Category 1 or 2, still sampled in the horizon
    D = P[P["category"].isin(["1", "2"]) & P["horizon_complete"] & P["rated_in_horizon"]].copy()
    train_cut = pd.Timestamp(a.train_end) - pd.DateOffset(months=H)            # outcome window must close before train_end
    tr = D[D["window_end"] <= train_cut]; te = D[D["window_end"] >= a.test_start]
    res["task"] = {"train_rows": int(len(tr)), "train_positive_pct": round(100 * float(tr["y"].mean()), 2), "train_last_window_end": str(tr["window_end"].max().date()),
                   "test_rows": int(len(te)), "test_positive_pct": round(100 * float(te["y"].mean()), 2), "test_window_ends": [str(te["window_end"].min().date()), str(te["window_end"].max().date())],
                   "test_units": int(te["u"].nunique()), "test_new_failures": int(te["y"].sum())}
    print("\nTask:", json.dumps(res["task"]))

    # a feature that does not exist yet in the training years (e.g. CFU counts, which start in FY2022-23) cannot be learned from
    empty = [f for f in feats if tr[f].notna().sum() == 0]
    feats = [f for f in feats if f not in empty]; res["features_dropped_empty_in_training"] = empty; res["features"] = feats
    Xtr, ytr, Xte, yte = tr[feats], tr["y"].to_numpy(), te[feats], te["y"].to_numpy()
    lr = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=2000, C=0.5)).fit(Xtr, ytr)
    gb = HistGradientBoostingClassifier(max_depth=4, learning_rate=0.05, max_iter=300, l2_regularization=1.0, min_samples_leaf=40, random_state=a.seed).fit(Xtr, ytr)
    gb_nofeat = HistGradientBoostingClassifier(max_depth=4, learning_rate=0.05, max_iter=300, l2_regularization=1.0, min_samples_leaf=40, random_state=a.seed).fit(Xtr[[f for f in feats if f != "projection_logit"]], ytr)
    scores = {"currently Category 2 (flag)": te["is_cat2"].to_numpy(float),
              "trailing 52-week rate": te["rate52"].fillna(0).to_numpy(),
              "positives to spare (fewest first)": (-te["spare3_frac"]).to_numpy(),
              "binomial projection": te["projection"].to_numpy(),
              "logistic regression": lr.predict_proba(Xte)[:, 1],
              "gradient boosting, no projection feature": gb_nofeat.predict_proba(Xte[[f for f in feats if f != "projection_logit"]])[:, 1],
              "gradient boosting": gb.predict_proba(Xte)[:, 1]}
    g = te["window_end"].to_numpy()
    rows = []
    for name, s in scores.items():
        rec, prec = top_share_metrics(yte, s, g, 0.10)
        rows.append({"scorer": name, "auroc": round(roc_auc_score(yte, s), 3), "avg_precision": round(average_precision_score(yte, s), 3),
                     "recall_top10pct": round(rec, 3), "precision_top10pct": round(prec, 3),
                     "brier": round(brier_score_loss(yte, np.clip(s, 0, 1)), 4) if name in ("binomial projection", "logistic regression", "gradient boosting", "gradient boosting, no projection feature") else None})
    M = pd.DataFrame(rows); M.to_csv(a.out / f"early_warning_metrics_h{H}.csv", index=False)
    print(f"\nEarly warning, horizon {H} months, test window ends {res['task']['test_window_ends']}:\n", M.to_string(index=False))
    res["metrics"] = rows
    c2 = te["is_cat2"] == 1
    res["cat2_flag"] = {"flagged_pct": round(100 * float(c2.mean()), 1), "precision": round(float(te.loc[c2, "y"].mean()), 3), "recall": round(float(te.loc[c2, "y"].sum() / te["y"].sum()), 3)}
    print("Category 2 flag:", res["cat2_flag"])

    # by product class
    te = te.assign(gb=scores["gradient boosting"], proj=scores["binomial projection"])
    bc = []
    for c, d in te.groupby("product_class"):
        if d["y"].sum() >= 10 and d["y"].nunique() == 2:
            bc.append({"product_class": c, "rows": len(d), "new_failures": int(d["y"].sum()), "base_pct": round(100 * d["y"].mean(), 2),
                       "auroc_projection": round(roc_auc_score(d["y"], d["proj"]), 3), "auroc_gb": round(roc_auc_score(d["y"], d["gb"]), 3),
                       "ap_projection": round(average_precision_score(d["y"], d["proj"]), 3), "ap_gb": round(average_precision_score(d["y"], d["gb"]), 3)})
    BC = pd.DataFrame(bc); print("\nBy product class:\n", BC.to_string(index=False)); res["by_class"] = bc
    # calibration of the gradient boosting model, test period
    te["bin"] = pd.qcut(te["gb"].rank(method="first"), 10, labels=False)
    cal = te.groupby("bin").agg(mean_pred=("gb", "mean"), observed=("y", "mean"), n=("y", "size")).round(4)
    print("\nCalibration (gradient boosting, deciles of predicted risk):\n", cal.to_string()); res["calibration_gb"] = cal.reset_index().to_dict(orient="records")
    # which features carry the model: permutation importance on the test period (AUROC drop)
    from sklearn.inspection import permutation_importance
    pi = permutation_importance(gb, Xte, yte, scoring="average_precision", n_repeats=5, random_state=a.seed)
    imp = pd.DataFrame({"feature": feats, "ap_drop": pi.importances_mean}).sort_values("ap_drop", ascending=False).head(12).round(4)
    print("\nPermutation importance (drop in average precision), top 12:\n", imp.to_string(index=False)); res["importance_top"] = imp.to_dict(orient="records")
    te[["establishment_id", "product_class", "window_end", "category", "n52", "pos52", "spare3", "projection", "gb", "y"]].to_parquet(a.out / f"early_warning_test_scores_h{H}.parquet", index=False)

    # uncertainty: month-ends of one establishment are not independent, so resample whole establishments
    rng = np.random.default_rng(a.seed); est = te["establishment_id"].to_numpy(); uniq = np.unique(est)
    pos_by_est = {e: np.flatnonzero(est == e) for e in uniq}
    lrs = scores["logistic regression"]; prj = scores["binomial projection"]; gbs = scores["gradient boosting"]
    boot = []
    for _ in range(a.bootstrap):
        ix = np.concatenate([pos_by_est[e] for e in rng.choice(uniq, size=len(uniq), replace=True)])
        yy = yte[ix]
        if yy.min() == yy.max():
            continue
        boot.append({"auroc_proj": roc_auc_score(yy, prj[ix]), "auroc_lr": roc_auc_score(yy, lrs[ix]), "auroc_gb": roc_auc_score(yy, gbs[ix]),
                     "ap_proj": average_precision_score(yy, prj[ix]), "ap_lr": average_precision_score(yy, lrs[ix]), "ap_gb": average_precision_score(yy, gbs[ix])})
    B = pd.DataFrame(boot); B["d_auroc_gb"] = B["auroc_gb"] - B["auroc_proj"]; B["d_ap_gb"] = B["ap_gb"] - B["ap_proj"]; B["d_auroc_lr"] = B["auroc_lr"] - B["auroc_proj"]; B["d_ap_lr"] = B["ap_lr"] - B["ap_proj"]
    ci = B.quantile([0.025, 0.5, 0.975]).T.round(3); ci.columns = ["lo", "median", "hi"]
    print(f"\nEstablishment-clustered bootstrap, {len(B)} resamples of {len(uniq)} establishments (95% interval):\n", ci.to_string())
    res["bootstrap_ci"] = {k: {c: float(v) for c, v in row.items()} for k, row in ci.iterrows()}; res["bootstrap_establishments"] = int(len(uniq))

    # lead time: for each new failure in the test period, how early was the unit on a top-10% watch list?
    A = P[(P["window_end"] >= a.test_start) & P["category"].isin(["1", "2"])].copy()
    A["s_proj"] = A["projection"]; A["s_gb"] = gb.predict_proba(A[feats])[:, 1]
    for col in ("s_proj", "s_gb"):
        rk = A.groupby("window_end")[col].rank(method="first", ascending=False); k = np.ceil(A.groupby("window_end")[col].transform("size") * 0.10)
        A["watch_" + col] = rk <= k
    A["watch_cat2"] = A["category"] == "2"
    allc = P[P["window_end"] >= pd.Timestamp(a.test_start) - pd.DateOffset(months=1)][["u", "window_end", "category"]].sort_values(["u", "window_end"])
    allc["prev"] = allc.groupby("u")["category"].shift(1)
    first_test = sorted(P.loc[P["window_end"] >= a.test_start, "window_end"].unique())
    onset = allc[(allc["category"] == "3") & (allc["prev"].isin(["1", "2", "NA"])) & (allc["window_end"] >= first_test[min(H, len(first_test) - 1)])]
    ends_sorted = sorted(P["window_end"].unique()); pos_of = {e: i for i, e in enumerate(ends_sorted)}
    Aidx = A.set_index(["u", "window_end"])
    lead_rows = []
    for u, e, prev in zip(onset["u"], onset["window_end"], onset["prev"]):
        i = pos_of[e]; rec = {"u": u, "onset": e, "prev_category": prev}
        for col in ("watch_s_proj", "watch_s_gb", "watch_cat2"):
            lead = 0
            for back in range(1, H + 1):
                key = (u, ends_sorted[i - back])
                if key in Aidx.index and bool(Aidx.loc[key, col]):
                    lead = back
            rec[col] = lead                                                    # earliest month (within H) the unit was on the list; 0 = never
        lead_rows.append(rec)
    L = pd.DataFrame(lead_rows)
    lead_summary = {"new_failures": int(len(L)), "from_unrated_NA": int((L["prev_category"] == "NA").sum())}
    for col, name in [("watch_s_proj", "projection_top10pct"), ("watch_s_gb", "gradient_boosting_top10pct"), ("watch_cat2", "category2_flag")]:
        lead_summary[name] = {"on_list_at_least_1_month_before_pct": round(100 * float((L[col] >= 1).mean()), 1),
                              "at_least_3_months_before_pct": round(100 * float((L[col] >= 3).mean()), 1),
                              f"at_least_{H}_months_before_pct": round(100 * float((L[col] >= H).mean()), 1)}
    print("\nLead time for new Category 3 entries in the test period:\n", json.dumps(lead_summary, indent=1)); res["lead_time"] = lead_summary
    sizes = A.groupby("window_end").size(); res["watch_list_size_per_month"] = {"units_rated_1_or_2_median": float(sizes.median()), "top10pct_median": float(np.ceil(sizes * 0.10).median()),
                                                                              "category2_median": float(A.groupby("window_end")["watch_cat2"].sum().median())}
    print("Watch-list sizes per month:", res["watch_list_size_per_month"])
    (a.out / f"early_warning_summary_h{H}.json").write_text(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    pd.set_option("display.width", 220); pd.set_option("display.max_columns", 40)
    main()
