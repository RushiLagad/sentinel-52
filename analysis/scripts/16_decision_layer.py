#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-27, run against
# the real FSIS scores and the seeded synthetic inventory the same day.
# -----------------------------------------------------------------------------
"""Turn a risk score into one of four actions on a lot, and cost the policy.

This is the decision layer. It is the part of the project that is about the food
bank rather than about FSIS, and the part where the challenge question's four
objectives actually collide: protect health, keep food available, support food
security, do not waste edible food.

WHAT IS REAL AND WHAT IS NOT
  Risk scores, categories, outcomes (`y`), establishments: real FSIS data.
  Lots, pounds, destinations, shelf life: SIMULATED by 14_build_synthetic_inventory.py.
  Therefore every pounds-denominated number this script emits is simulated, and
  every output it writes carries `pounds_are_synthetic: true`. A reader who takes
  the poundage as a measurement of a real food bank has been misled. The ranking,
  the error rates and the equity direction do not depend on the simulation's
  scale; the absolute pounds do.

THE FOUR ACTIONS
  distribute now         low risk, ship to pantries as normal
  prioritize             acceptable risk but little shelf life left; move it first
  hold for review        moderate risk, and there is both review capacity and
                         enough shelf life to wait. HIGH-CONSEQUENCE.
  divert                 high risk; away from direct pantry distribution and into
                         a cooked-meal channel, where a validated cook step
                         applies. HIGH-CONSEQUENCE.

  Diversion is the food-bank-specific move and it is why this is not simply a
  recall simulator. A plant with a bad sampling trajectory does not make its
  product inedible; it makes uncooked distribution the wrong channel for it.
  Cooked-meal partners have finite capacity, so diverted pounds beyond that
  capacity are discarded, and discard is therefore a consequence of capacity
  rather than an assumption.

WHY THE TRANSPARENT PROJECTION IS THE DEFAULT SCORER
  05c_calibration.py measured both scorers at three horizons. At the 3-month
  horizon the binomial projection is well calibrated (ECE 0.0056, top decile
  predicted 0.342 against observed 0.300) while gradient boosting overpredicts
  the top decile badly (0.437 against 0.303, ECE 0.0213). A hold-or-divert
  decision acts on absolute probability, not on ranking, so calibration matters
  more here than the small AUROC advantage. Pass --scorer gb to compare.

NOTHING HERE IS A SAFETY VERDICT
  No output of this script says a food is safe or unsafe, and none of it is a
  regulatory determination. It allocates attention and names what each choice
  costs. Hold and divert are marked high-consequence and carry the evidence that
  would reverse them, because a human makes the call.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ACTIONS = ["distribute_now", "prioritize", "hold_for_review", "divert"]
HIGH_CONSEQUENCE = {"hold_for_review", "divert"}

# Feeding America's convention for converting donated weight to meals served.
# Stated here because every "meals" figure below depends on it.
LBS_PER_MEAL = 1.2


# --------------------------------------------------------------------------- #
# scenarios
# --------------------------------------------------------------------------- #
# divert_at / hold_at are thresholds on the chosen scorer's probability.
# review_capacity_per_week caps holds. cook_capacity_lbs_per_week caps diversion
# before discard. food_security_weight in [0, 1] raises the hold and divert
# thresholds for destinations in the most vulnerable SVI quartile, which protects
# supply to high-need areas at the cost of accepting more risk there. That
# trade-off is reported, never hidden: see the equity table.
SCENARIOS = {
    "rule_based_category": dict(
        label="Rule-based (status quo): hold anything from a Category 2 or 3 plant",
        kind="rule", divert_at=None, hold_at=None,
        review_capacity_per_week=None, cook_capacity_lbs_per_week=None,
        food_security_weight=0.0),
    "conservative": dict(
        label="Conservative: hold on weak signals",
        kind="score", divert_at=0.30, hold_at=0.05,
        # Unlimited review capacity is what makes this scenario "conservative";
        # the cook channel is held at the same size as the others so the only
        # variable between the three score scenarios is the policy itself.
        review_capacity_per_week=None, cook_capacity_lbs_per_week=12000,
        food_security_weight=0.0),
    # hold_at=None on these two means "derive it from review capacity", which is
    # what the name promises. Hardcoding a threshold and then reporting that it
    # used 28 percent of capacity would make the label untrue.
    "capacity_matched": dict(
        label="Capacity-matched: hold threshold derived from review capacity",
        kind="score", divert_at=0.30, hold_at=None,
        review_capacity_per_week=6, cook_capacity_lbs_per_week=12000,
        food_security_weight=0.0),
    "food_security_weighted": dict(
        label="Food-security weighted: supply to high-need counties protected",
        kind="score", divert_at=0.30, hold_at=None,
        review_capacity_per_week=6, cook_capacity_lbs_per_week=12000,
        food_security_weight=1.0),
}


def threshold_for_capacity(d: pd.DataFrame, scorer: str, divert_at: float,
                           capacity_per_week: int) -> float:
    """The hold threshold that fills the review queue to capacity and no further.

    Searched rather than solved, because the mapping from threshold to queue
    length is not monotone once shelf life diverts some holds and the weekly cap
    releases others. Returns the lowest threshold whose queue still fits, so the
    queue is as sensitive as the capacity allows.
    """
    weeks = max(d["week_pre"].nunique(), 1)
    budget = capacity_per_week * weeks
    scored = d["scored"]
    for t in np.round(np.arange(0.01, divert_at + 0.001, 0.01), 3):
        n = int((scored & (d[scorer] >= t) & (d[scorer] < divert_at)).sum())
        if n <= budget:
            return float(t)
    return float(divert_at)


def reversal_evidence(row: pd.Series, scorer: str) -> str:
    """What would change this recommendation. Required by R4.4."""
    bits = []
    if row["action"] == "divert":
        bits.append(f"{scorer} falling below {row['divert_at']:.2f}")
    else:
        bits.append(f"{scorer} falling below {row['hold_at']:.2f}")
    if pd.notna(row.get("category")) and str(row["category"]) in {"2", "3"}:
        bits.append("FSIS posting a Category 1 rating for this plant")
    if pd.notna(row.get("pos52")) and row["pos52"] > 0:
        bits.append("a clean 52-week window at this plant")
    if pd.notna(row.get("score_age_days")) and row["score_age_days"] > 60:
        bits.append(f"fresher sampling (this score is {int(row['score_age_days'])} days old)")
    return "; ".join(bits)


# --------------------------------------------------------------------------- #
# joining lots to scores
# --------------------------------------------------------------------------- #
def attach_scores(lots: pd.DataFrame, scores: pd.DataFrame, max_age_days: int) -> pd.DataFrame:
    """As-of backward join: a lot can only know what was published before it arrived.

    This is the correct join and it is not the convenient one. Using the score
    from the window that *contains* the receipt date would leak information the
    food bank could not have had, and would flatter every metric below.
    """
    L = lots.copy()
    L["received_date"] = pd.to_datetime(L["received_date"])
    L["use_by_date"] = pd.to_datetime(L["use_by_date"])
    S = scores.copy()
    S["window_end"] = pd.to_datetime(S["window_end"])

    # The two sources arrive with different dtypes for the join keys (the parquet
    # carries nullable Int32, the CSV plain int64), and merge_asof refuses to
    # match across them. Normalise rather than let it fail at the judges' end.
    for f in (L, S):
        f["establishment_id"] = f["establishment_id"].astype("int64")
        f["product_class"] = f["product_class"].astype(str)
    # `category` is a string in the current build, but an earlier vintage carried
    # it as an integer, and merge_asof turns an integer column with unmatched
    # rows into floats. "2.0" would then silently fail the Category 2-or-3 test
    # and the rule-based baseline would hold nothing at all, which is the kind of
    # bug that looks like a finding. Normalise it.
    S["category"] = (S["category"].astype("string")
                     .str.replace(r"\.0$", "", regex=True).str.strip())

    L = L.sort_values("received_date")
    S = S.sort_values("window_end")
    out = pd.merge_asof(
        L, S, left_on="received_date", right_on="window_end",
        by=["establishment_id", "product_class"], direction="backward",
    )
    out["score_age_days"] = (out["received_date"] - out["window_end"]).dt.days
    # A score nobody could still rely on is not a score. Unscored lots are
    # reported separately rather than quietly treated as low risk.
    out["scored"] = out["window_end"].notna() & (out["score_age_days"] <= max_age_days)
    out["week_pre"] = out["received_date"].dt.to_period("W").astype(str)
    return out


# --------------------------------------------------------------------------- #
# the policy
# --------------------------------------------------------------------------- #
def apply_policy(df: pd.DataFrame, cfg: dict, scorer: str, prioritize_days: int,
                 min_days_to_distribute: int = 3) -> pd.DataFrame:
    """Assign one action per lot, honouring shelf life and both capacities."""
    d = df.copy()
    d["hold_at"] = cfg["hold_at"] if cfg["hold_at"] is not None else np.nan
    d["divert_at"] = cfg["divert_at"] if cfg["divert_at"] is not None else np.nan

    # Food-security weighting: for the most vulnerable quartile of destinations,
    # require a stronger signal before taking food away from them.
    w = cfg["food_security_weight"]
    if w and cfg["kind"] == "score":
        top = d["svi_quartile"] == "Q4 most vulnerable"
        d.loc[top, "hold_at"] = d.loc[top, "hold_at"] * (1 + w)
        d.loc[top, "divert_at"] = d.loc[top, "divert_at"] * (1 + 0.5 * w)

    if cfg["kind"] == "rule":
        flag = d["category"].astype("string").isin(["2", "3"])
        d["action"] = np.where(flag, "hold_for_review", "distribute_now")
        d["driver"] = np.where(flag, "FSIS Category 2 or 3 at this plant", "not Category 2 or 3")
    else:
        s = d[scorer]
        d["action"] = "distribute_now"
        d["driver"] = f"{scorer} below {cfg['hold_at']}"
        hold = d["scored"] & (s >= d["hold_at"]) & (s < d["divert_at"])
        div = d["scored"] & (s >= d["divert_at"])
        d.loc[hold, "action"] = "hold_for_review"
        d.loc[hold, "driver"] = f"{scorer} at or above the hold threshold"
        d.loc[div, "action"] = "divert"
        d.loc[div, "driver"] = f"{scorer} at or above the divert threshold"
        # An unscored lot is not assumed safe; it is surfaced for review when
        # there is capacity, and distributed with the gap named when there is not.
        d.loc[~d["scored"], "driver"] = "no recent sampling for this plant and product"

    # Shelf life gates holding. A lot with days_left below the review turnaround
    # cannot wait for a review, so the choice collapses to distribute or divert.
    d["days_left"] = (d["use_by_date"] - d["received_date"]).dt.days
    cannot_wait = (d["action"] == "hold_for_review") & (d["days_left"] < prioritize_days)
    d.loc[cannot_wait, "action"] = "divert"
    d.loc[cannot_wait, "driver"] = d.loc[cannot_wait, "driver"] + \
        f"; too little shelf life ({prioritize_days}d review turnaround) to hold"

    # Short shelf life on an otherwise distributable lot: move it first.
    soon = (d["action"] == "distribute_now") & (d["days_left"] <= prioritize_days)
    d.loc[soon, "action"] = "prioritize"
    d.loc[soon, "driver"] = d.loc[soon, "driver"] + f"; {prioritize_days}d or less of shelf life"

    d["week"] = d["received_date"].dt.to_period("W").astype(str)

    # Review capacity: keep the highest-consequence holds, release the rest.
    # Ranking by risk times pounds, because a bad signal on a pallet matters more
    # than the same signal on a single case.
    cap = cfg["review_capacity_per_week"]
    if cap is not None:
        d["_rank_by"] = d[scorer].fillna(0) * d["pounds"]
        h = d[d["action"] == "hold_for_review"]
        keep = (h.sort_values(["week", "_rank_by"], ascending=[True, False])
                 .groupby("week").head(cap).index)
        released = h.index.difference(keep)
        d.loc[released, "action"] = "prioritize"
        d.loc[released, "driver"] = d.loc[released, "driver"] + \
            "; released because weekly review capacity was already full"
        d.drop(columns="_rank_by", inplace=True)

    # Food loss has exactly two mechanisms here, and both are mechanical rather
    # than assumed, so no spoilage fraction has been invented.
    d["discarded"] = False
    d["discard_reason"] = ""

    # 1. A hold consumes `prioritize_days` of shelf life. If what remains after
    #    review is less than the time needed to move the lot through the pantry
    #    network, the hold has destroyed the food even though nobody discarded it
    #    deliberately. This is the cost that makes "hold on weak signals"
    #    expensive, and leaving it out is what made an earlier version of this
    #    script show a conservative policy as free.
    held = d["action"] == "hold_for_review"
    spoiled = held & ((d["days_left"] - prioritize_days) < min_days_to_distribute)
    d.loc[spoiled, "discarded"] = True
    d.loc[spoiled, "discard_reason"] = "shelf life exhausted by the review hold"

    # 2. Diverted pounds beyond the cooked-meal channel's weekly capacity.
    ccap = cfg["cook_capacity_lbs_per_week"]
    if ccap is not None:
        dv = d[d["action"] == "divert"].sort_values(["week", "pounds"], ascending=[True, False])
        cum = dv.groupby("week")["pounds"].cumsum()
        over = cum[cum > ccap].index
        d.loc[over, "discarded"] = True
        d.loc[over, "discard_reason"] = "cooked-meal channel at capacity"
    return d


# --------------------------------------------------------------------------- #
# costing a policy
# --------------------------------------------------------------------------- #
def score_policy(d: pd.DataFrame, name: str, cfg: dict) -> dict:
    """Error rates against the real outcome, and food loss in shared units."""
    acted = d["action"].isin(HIGH_CONSEQUENCE)
    y = d["y"].fillna(0).astype(bool)          # did this plant go on to elevated risk
    tp, fp = int((acted & y).sum()), int((acted & ~y).sum())
    fn, tn = int((~acted & y).sum()), int((~acted & ~y).sum())

    weeks = max(d["week"].nunique(), 1)
    holds_per_week = float((d["action"] == "hold_for_review").sum()) / weeks

    lbs = d.groupby("action")["pounds"].sum()
    discarded_lbs = float(d.loc[d["discarded"], "pounds"].sum())
    distributed_lbs = float(lbs.get("distribute_now", 0.0) + lbs.get("prioritize", 0.0))
    diverted_lbs = float(lbs.get("divert", 0.0))

    # The two error types in the same units, which is the whole point of R7.3.
    #
    # avoidable_loss: edible food discarded from a plant that did NOT go on to
    #   elevated risk. This is the cost of a false alarm and it is a real loss.
    # exposure: food distributed uncooked from a plant whose sampling later did
    #   deteriorate. This is NOT a count of illnesses and must never be reported
    #   as one. FSIS data cannot attribute illness to an establishment, and this
    #   project does not. It is the quantity of food that went out uncooked from
    #   plants that a better-aimed policy would have caught, which is what
    #   the number actually measures.
    avoidable_loss_lbs = float(d.loc[d["discarded"] & ~y, "pounds"].sum())
    exposure_lbs = float(d.loc[~acted & y, "pounds"].sum())

    return {
        "scenario": name,
        "label": cfg["label"],
        "lots": int(len(d)),
        "lots_unscored": int((~d["scored"]).sum()),
        "hold_at": cfg["hold_at"], "divert_at": cfg["divert_at"],
        "review_capacity_per_week": cfg["review_capacity_per_week"],
        "cook_capacity_lbs_per_week": cfg["cook_capacity_lbs_per_week"],
        "food_security_weight": cfg["food_security_weight"],
        "n_distribute_now": int((d["action"] == "distribute_now").sum()),
        "n_prioritize": int((d["action"] == "prioritize").sum()),
        "n_hold_for_review": int((d["action"] == "hold_for_review").sum()),
        "n_divert": int((d["action"] == "divert").sum()),
        "precision": round(tp / (tp + fp), 4) if tp + fp else None,
        "recall": round(tp / (tp + fn), 4) if tp + fn else None,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "pounds_distributed": round(distributed_lbs, 1),
        "pounds_held": round(float(lbs.get("hold_for_review", 0.0)), 1),
        "pounds_diverted": round(diverted_lbs, 1),
        "pounds_discarded": round(discarded_lbs, 1),
        "avoidable_loss_lbs": round(avoidable_loss_lbs, 1),
        "avoidable_loss_meals": int(avoidable_loss_lbs / LBS_PER_MEAL),
        "exposure_lbs": round(exposure_lbs, 1),
        "exposure_meals": int(exposure_lbs / LBS_PER_MEAL),
        # (b) Is this policy actually executable? The status quo turns out not
        # to be, and that is the strongest argument in the project.
        "holds_per_week_required": round(holds_per_week, 2),
        "review_capacity_exceeded_by": (
            None if cfg["review_capacity_per_week"] is None
            else round(holds_per_week / cfg["review_capacity_per_week"], 1)),
        "pounds_are_synthetic": True,
    }


def equity_table(d: pd.DataFrame, name: str) -> pd.DataFrame:
    """Hold and divert rates by destination SVI quartile, reported both ways.

    R6.3 asks for the result whichever way it comes out, so this returns the
    table and the disparity, and makes no attempt to optimise it away.
    """
    g = d.groupby("svi_quartile", observed=True)
    t = pd.DataFrame({
        "scenario": name,
        "lots": g["lot_id"].size(),
        "pounds_offered": g["pounds"].sum().round(1),
        "pounds_distributed": d[d["action"].isin(["distribute_now", "prioritize"])]
            .groupby("svi_quartile", observed=True)["pounds"].sum().round(1),
        "pounds_withheld": d[d["action"].isin(HIGH_CONSEQUENCE)]
            .groupby("svi_quartile", observed=True)["pounds"].sum().round(1),
    }).reset_index()
    t[["pounds_distributed", "pounds_withheld"]] = \
        t[["pounds_distributed", "pounds_withheld"]].fillna(0.0)
    t["withheld_pct"] = (100 * t["pounds_withheld"] / t["pounds_offered"]).round(2)
    t["share_of_all_distribution_pct"] = \
        (100 * t["pounds_distributed"] / t["pounds_distributed"].sum()).round(2)
    t["pounds_are_synthetic"] = True
    return t


def frontier(d0: pd.DataFrame, cfg: dict, scorer: str, prioritize_days: int,
             grid: np.ndarray, divert_ratio: float = 2.5) -> pd.DataFrame:
    """Sweep the hold threshold. R3.5: show a frontier, not one operating point.

    The choice between the two error types is a value judgement about whose risk
    matters more, so the script declines to pick a point on this curve.
    """
    rows = []
    for t in grid:
        # Both thresholds move together. Sweeping the hold threshold alone leaves
        # the divert threshold fixed, and since diversion is what drives loss,
        # the loss axis then barely moves and the "frontier" is a precision-recall
        # curve wearing a disguise.
        c = dict(cfg)
        c["hold_at"] = float(t)
        c["divert_at"] = float(t * divert_ratio)
        m = score_policy(apply_policy(d0, c, scorer, prioritize_days), f"t={t:.3f}", c)
        rows.append({"hold_at": round(float(t), 4),
                     "divert_at": round(float(t * divert_ratio), 4),
                     "recall": m["recall"], "precision": m["precision"],
                     "pounds_distributed": m["pounds_distributed"],
                     "pounds_discarded": m["pounds_discarded"],
                     "avoidable_loss_meals": m["avoidable_loss_meals"],
                     "exposure_meals": m["exposure_meals"],
                     "pounds_are_synthetic": True})
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lots", type=Path, required=True, help="lots_synthetic.csv from script 14")
    ap.add_argument("--scores", type=Path, required=True,
                    help="early_warning_test_scores_h{H}.parquet from script 05")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--horizon", default="3", help="label only; must match --scores")
    ap.add_argument("--scorer", default="auto", choices=["auto", "projection", "gb"],
                    help="auto (the default) reads calibration_h{H}.json from --out and picks "
                         "whichever scorer is better calibrated AT THIS HORIZON. Hardcoding one "
                         "is a footgun: the projection wins at h3 and loses at h6.")
    ap.add_argument("--max-score-age-days", type=int, default=120,
                    help="older than this and the lot counts as unscored")
    ap.add_argument("--prioritize-days", type=int, default=7,
                    help="review turnaround; a lot with less shelf life than this cannot be held")
    ap.add_argument("--default-scenario", default="conservative", choices=list(SCENARIOS),
                    help="which scenario's per-lot recommendations to write to t23 for the app. "
                         "Deliberately a flag and not a computed answer: picking a point on the "
                         "frontier is a value judgement about whose risk counts, not an "
                         "optimisation (R3.5)")
    ap.add_argument("--min-days-to-distribute", type=int, default=3,
                    help="days needed to move a released lot through the pantry network; "
                         "a hold that leaves less than this has destroyed the food")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    H = a.horizon

    # Which scorer, decided by measurement rather than by preference. A
    # hold-or-divert decision acts on an absolute probability, so the scorer with
    # the lower expected calibration error at THIS horizon is the right one, even
    # when the other has the better AUROC.
    scorer_choice = {"reason": "", "ece": {}}
    if a.scorer == "auto":
        cal = a.out / f"calibration_h{H}.json"
        if cal.exists():
            c = json.loads(cal.read_text())
            e = {k: float(v["ece"]) for k, v in c.get("scorers", {}).items()
                 if isinstance(v, dict) and "ece" in v}
            if {"projection", "gb"} <= set(e):
                a.scorer = min(("projection", "gb"), key=lambda k: e[k])
                scorer_choice = {
                    "reason": (f"auto: lower expected calibration error at h{H} "
                               f"(projection {e['projection']:.4f}, gb {e['gb']:.4f})"),
                    "ece": e}
        if a.scorer == "auto":
            a.scorer = "projection"
            scorer_choice = {"reason": (f"auto fell back to the projection: no usable "
                                        f"calibration_h{H}.json in {a.out}, so the better "
                                        f"calibrated scorer could not be determined. Run "
                                        f"05c_calibration.py first."), "ece": {}}
        print(f"scorer: {a.scorer}  ({scorer_choice['reason']})\n")

    lots = pd.read_csv(a.lots)
    if not bool(lots.get("is_synthetic", pd.Series([False])).all()):
        raise SystemExit("every lot must be flagged is_synthetic; refusing to imply real inventory")
    scores = pd.read_parquet(a.scores)

    d0 = attach_scores(lots, scores, a.max_score_age_days)
    # Quartiles of destination vulnerability, fixed once so every scenario is
    # measured against the same bins.
    d0["svi_quartile"] = pd.qcut(
        d0["dest_svi_overall"], 4,
        labels=["Q1 least vulnerable", "Q2", "Q3", "Q4 most vulnerable"])

    print(f"{len(d0)} lots, {d0['pounds'].sum():,.0f} simulated lb, "
          f"{d0['establishment_id'].nunique()} plants, "
          f"{d0['dest_county'].nunique()} destination counties")
    print(f"scored within {a.max_score_age_days} days: {int(d0['scored'].sum())} "
          f"({100*d0['scored'].mean():.1f}%); median score age "
          f"{d0.loc[d0['scored'], 'score_age_days'].median():.0f} days")
    print(f"outcome base rate among scored lots: {100*d0.loc[d0['scored'],'y'].mean():.2f}%\n")

    summaries, equities, assigned = [], [], {}
    scenarios = {}
    for name, cfg in SCENARIOS.items():
        cfg = dict(cfg)
        if cfg["kind"] == "score" and cfg["hold_at"] is None:
            cfg["hold_at"] = threshold_for_capacity(
                d0, a.scorer, cfg["divert_at"], cfg["review_capacity_per_week"])
            cfg["hold_at_derived_from_capacity"] = True
        scenarios[name] = cfg

    for name, cfg in scenarios.items():
        d = apply_policy(d0, cfg, a.scorer, a.prioritize_days, a.min_days_to_distribute)
        m = score_policy(d, name, cfg)
        summaries.append(m)
        equities.append(equity_table(d, name))
        assigned[name] = d
        print(f"{cfg['label']}")
        print(f"   hold {m['n_hold_for_review']:>4}  divert {m['n_divert']:>4}  "
              f"prioritize {m['n_prioritize']:>4}  distribute {m['n_distribute_now']:>4}")
        print(f"   precision {m['precision']}  recall {m['recall']}  "
              f"distributed {m['pounds_distributed']:,.0f} lb  "
              f"discarded {m['pounds_discarded']:,.0f} lb")
        feas = ("" if m["review_capacity_exceeded_by"] is None
                else f"   reviews needed {m['holds_per_week_required']:.1f}/wk "
                     f"({m['review_capacity_exceeded_by']}x capacity)")
        print(f"   avoidable loss {m['avoidable_loss_meals']:,} meals   "
              f"exposure {m['exposure_meals']:,} meals")
        print(f"   holds required {m['holds_per_week_required']:.1f}/week{feas}\n")

    S = pd.DataFrame(summaries)
    E = pd.concat(equities, ignore_index=True)
    F = frontier(d0, scenarios["capacity_matched"], a.scorer, a.prioritize_days,
                 np.round(np.arange(0.02, 0.31, 0.02), 3))

    # Disparity check, stated whichever way it comes out (R6.3, R6.4).
    disp = []
    for name in scenarios:
        e = E[E["scenario"] == name].set_index("svi_quartile")
        q4 = float(e.loc["Q4 most vulnerable", "withheld_pct"])
        q1 = float(e.loc["Q1 least vulnerable", "withheld_pct"])
        disp.append({
            "scenario": name,
            "withheld_pct_most_vulnerable": q4,
            "withheld_pct_least_vulnerable": q1,
            "difference_pct_points": round(q4 - q1, 2),
            "hold_threshold": scenarios[name]["hold_at"],
            "direction": ("falls harder on high-need counties" if q4 - q1 > 1
                          else "falls harder on low-need counties" if q4 - q1 < -1
                          else "no material difference"),
        })

    # Dominance. If one scenario is at least as good as another on recall AND on
    # both costs, the other is simply worse and there is no trade-off to debate.
    # The script reports this rather than choosing, because which non-dominated
    # point to stand on is the human's call.
    dominated = []
    for a_name in scenarios:
        ma = next(m for m in summaries if m["scenario"] == a_name)
        for b_name in scenarios:
            if a_name == b_name:
                continue
            mb = next(m for m in summaries if m["scenario"] == b_name)
            if ma["recall"] is None or mb["recall"] is None:
                continue
            if (mb["recall"] >= ma["recall"]
                    and mb["avoidable_loss_meals"] <= ma["avoidable_loss_meals"]
                    and mb["exposure_meals"] <= ma["exposure_meals"]
                    and (mb["recall"] > ma["recall"]
                         or mb["avoidable_loss_meals"] < ma["avoidable_loss_meals"]
                         or mb["exposure_meals"] < ma["exposure_meals"])):
                dominated.append({
                    "dominated": a_name, "by": b_name,
                    "why": (f"{b_name} reaches recall {mb['recall']} against "
                            f"{ma['recall']} while destroying "
                            f"{ma['avoidable_loss_meals'] - mb['avoidable_loss_meals']:,} "
                            f"fewer meals"),
                })

    # The per-lot recommendation set the app renders, with reversal evidence.
    best = assigned[a.default_scenario].copy()
    best["high_consequence"] = best["action"].isin(HIGH_CONSEQUENCE)
    best["reversal_evidence"] = ""
    hc = best["high_consequence"]
    best.loc[hc, "reversal_evidence"] = best[hc].apply(
        reversal_evidence, axis=1, scorer=a.scorer)
    # R4.6: the opposite action and its own cost, so the user sees a choice.
    best["alternative_action"] = np.where(hc, "distribute_now", "hold_for_review")
    best["requires_human_confirmation"] = hc

    cols = ["lot_id", "is_synthetic", "establishment_id", "establishment_number",
            "establishment_name", "product_class", "received_date", "use_by_date",
            "days_left", "pounds", "dest_county", "dest_svi_overall", "svi_quartile",
            "category", "n52", "pos52", a.scorer, "scored", "score_age_days",
            "action", "driver", "high_consequence", "requires_human_confirmation",
            "alternative_action", "reversal_evidence", "discarded", "discard_reason"]
    best[[c for c in cols if c in best.columns]].to_csv(
        a.out / f"t23_lot_actions_h{H}.csv", index=False)
    S.to_csv(a.out / f"t20_scenarios_h{H}.csv", index=False)
    E.to_csv(a.out / f"t21_equity_by_svi_quartile_h{H}.csv", index=False)
    F.to_csv(a.out / f"t22_frontier_h{H}.csv", index=False)

    res = {
        "horizon_months": int(H), "scorer": a.scorer,
        "scorer_selection": scorer_choice,
        "scorer_rationale": ("A hold-or-divert decision acts on an absolute probability rather "
                             "than on a ranking, so the scorer is chosen by expected calibration "
                             "error at this horizon and not by AUROC. Which scorer that is "
                             "changes with the horizon: the projection is far better calibrated "
                             "at h3 (ECE 0.0056 against 0.0213) and worse at h6 (0.0092 against "
                             "0.0049)."),
        "threshold_caveat": ("hold_at and divert_at are thresholds on an absolute probability, so "
                             "they are horizon-specific and do not transfer. The same 0.05 means a "
                             "different thing against a 3-month outcome than against a 6-month "
                             "one, and the scenario ranking is not horizon-robust: re-running at "
                             "another horizon can reverse which scenario dominates."),
        "lbs_per_meal": LBS_PER_MEAL,
        "pounds_are_synthetic": True,
        "synthetic_note": ("lots, pounds, destinations and shelf life are simulated by "
                           "14_build_synthetic_inventory.py. Risk scores, FSIS categories and "
                           "outcomes are real. No pounds figure here measures a real food bank."),
        "inventory": {
            "lots": int(len(d0)), "pounds": round(float(d0["pounds"].sum()), 1),
            "plants": int(d0["establishment_id"].nunique()),
            "destination_counties": int(d0["dest_county"].nunique()),
            "scored_pct": round(100 * float(d0["scored"].mean()), 1),
            "median_score_age_days": float(d0.loc[d0["scored"], "score_age_days"].median()),
            "outcome_base_rate_pct": round(100 * float(d0.loc[d0["scored"], "y"].mean()), 2),
        },
        "default_scenario": a.default_scenario,
        "scenarios": summaries,
        "dominated_scenarios": dominated,
        "equity": json.loads(E.to_json(orient="records")),
        "disparity_check": disp,
        "frontier": json.loads(F.to_json(orient="records")),
        "how_to_read_these_numbers": [
            "These are a POLICY's performance on a simulated supply base of "
            f"{int(d0['establishment_id'].nunique())} plants, not the risk model's performance. "
            "The model's own metrics are in early_warning_summary_h*.json, measured on the "
            "full establishment panel. A policy evaluated on 52 high-volume suppliers will "
            "not have the same error rates as the model has across 578 establishments.",
            "The rule-based baseline uses the last posted FSIS category regardless of how old "
            "it is, because that is exactly what the status quo does: FSIS categories persist "
            "between quarterly postings and a food bank looks up the current one. The score "
            "policies, by contrast, treat a score older than the staleness limit as no score "
            "at all. The two are not held to the same standard on purpose.",
            "'exposure' is pounds or meals distributed uncooked from plants whose sampling "
            "later deteriorated. It is NOT a count of illnesses, and the FSIS licence forbids "
            "attributing illness to an establishment. Nothing here does.",
            "Food loss arises from two mechanical causes only, both derived from the simulated "
            "shelf life: a review hold that leaves too little shelf life to distribute, and "
            "diverted pounds beyond the cooked-meal channel's capacity. No spoilage rate has "
            "been assumed.",
        ],
        "guardrails": [
            "no output states that any food, lot or establishment is safe or unsafe",
            "no action is executed automatically; hold and divert require human confirmation",
            "no establishment is linked to any illness or outbreak anywhere in this script",
            "every pounds-denominated figure is simulated and flagged as such",
        ],
    }
    (a.out / f"decision_layer_h{H}.json").write_text(json.dumps(res, indent=1))

    if dominated:
        print("Dominated scenarios (worse on every axis, so not a trade-off):")
        for r in dominated:
            print(f"   {r['dominated']} is dominated by {r['by']}: {r['why']}")
        print()
    print("Disparity check (withheld share, most vulnerable quartile minus least):")
    for r in disp:
        print(f"   {r['scenario']:<24} {r['difference_pct_points']:+.2f} pp   {r['direction']}")
    print(f"\nper-lot recommendations written for scenario '{a.default_scenario}' "
          f"({int(best['high_consequence'].sum())} of {len(best)} lots high-consequence, "
          f"each carrying the evidence that would reverse it)")
    print(f"wrote {a.out / f'decision_layer_h{H}.json'} and t20-t23")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
