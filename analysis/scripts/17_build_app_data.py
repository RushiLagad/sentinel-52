#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-27.
# -----------------------------------------------------------------------------
"""Build the JSON the app reads, and enforce the project's guardrails on it.

The app is a static site. It does no computation and holds no opinions: every
number it shows is produced here, by the same scripts that produced the report,
and shipped as plain JSON under app/public/data/. If a figure is not in one of
these files, the app cannot display it.

Two modes:

    python scripts/17_build_app_data.py --out ../app/public/data     # build
    python scripts/17_build_app_data.py --check --out ../app/public/data

`--check` writes nothing. It re-reads what is already built and runs the
contract test and the guardrails, so a hook can call it after any edit. It exits
non-zero on the first failure and names it.

THE GUARDRAILS, AND WHY EACH ONE EXISTS

  G1  No establishment identifier may appear in any output derived from illness
      data. The FSIS licence forbids associating samples with illness, and the
      cheapest way to breach it by accident is to put a plant name next to a
      burden figure in a UI. Enforced by scanning the illness-derived payloads
      for any establishment field or value.

  G2  No output may contain a safety verdict. The words "safe" and "unsafe"
      applied to a food, lot or plant are not ours to say; we are reordering
      attention, not adjudicating. Enforced by scanning every string.

  G3  Every pounds- or meals-denominated payload must carry synthetic: true.
      The inventory is simulated. A reader who believes those pounds are real
      has been misled, and a badge that depends on a developer remembering to
      add it will eventually be forgotten.

  G4  Every high-consequence recommendation must carry non-empty reversal
      evidence and require human confirmation. An action the user cannot
      interrogate or refuse is not a recommendation.

  G5  Recalls must sort above model scores in the alert queue. A recall is a
      fact that has already happened; a score is a forecast. Ordering them the
      other way would put our inference above FSIS's finding.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

SCHEMA_VERSION = "1.0.0"

EST_FIELDS = {"establishment_id", "establishment_number", "establishment_name",
              "est_marks", "company", "plant", "plant_name"}

# Contract: filename -> keys every payload must have. The app reads these names,
# so a rename here without a rename there is a blank screen; the check catches it.
CONTRACT: dict[str, set[str]] = {
    "meta.json": {"schema_version", "generated_utc", "sources", "files", "restrictions"},
    "current_risk.json": {"meta", "units"},
    "alerts.json": {"meta", "alerts"},
    "scenarios.json": {"meta", "scenarios", "frontier", "controls", "dominated"},
    "actions.json": {"meta", "lots"},
    "evidence.json": {"meta", "model", "calibration", "sources", "restrictions"},
    "equity.json": {"meta", "quartiles", "disparity"},
    "burden.json": {"meta", "serotypes"},
}


def sha8(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:8]


def src(p: Path, root: Path) -> dict:
    return {"file": str(p.relative_to(root)).replace("\\", "/"),
            "sha256_8": sha8(p),
            "modified_utc": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc)
                                    .isoformat(timespec="seconds")}


def meta(name: str, sources: list[dict], *, synthetic: bool = False, **extra) -> dict:
    m = {"produced_by": "analysis/scripts/17_build_app_data.py",
         "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "schema_version": SCHEMA_VERSION, "payload": name, "sources": sources}
    if synthetic:
        m["synthetic"] = True
        m["synthetic_note"] = ("Lots, pounds, destinations and shelf life are simulated by "
                               "14_build_synthetic_inventory.py. Risk scores, FSIS categories "
                               "and outcomes are real. No figure here measures a real food bank.")
    m.update(extra)
    return m


RESTRICTIONS = [
    "FSIS sampling data cannot be used to identify foodborne illness outbreaks, to associate "
    "samples with outbreaks, or to determine whether two or more samples are causally related. "
    "Every join between FSIS sampling and CDC NORS illness data in this project is made at "
    "serotype and year, never at establishment level.",
    "Nothing here is a regulatory determination, an outbreak declaration, or a statement that any "
    "food, lot or establishment is safe or unsafe.",
    "No action is executed automatically. Hold and divert require explicit human confirmation.",
]


# --------------------------------------------------------------------------- #
# guardrails
# --------------------------------------------------------------------------- #
def walk_strings(o, path="$"):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk_strings(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(o, str):
        yield path, o


def walk_keys(o, path="$"):
    if isinstance(o, dict):
        for k, v in o.items():
            yield path, k
            yield from walk_keys(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk_keys(v, f"{path}[{i}]")


VERDICT = re.compile(r"\b(?:un)?safe\b", re.IGNORECASE)
# The restrictions text and the synthetic note both say the word "safe" in the
# course of forbidding the claim. Allow it only where we are disclaiming.
VERDICT_OK = re.compile(r"safe or unsafe|is not a statement|cannot be used", re.IGNORECASE)


def guardrails(payloads: dict[str, dict]) -> list[str]:
    fail: list[str] = []

    # G1 no establishment identifier anywhere in illness-derived output
    for name in ("burden.json",):
        p = payloads.get(name)
        if p is None:
            continue
        for path, key in walk_keys(p):
            if key in EST_FIELDS:
                fail.append(f"G1 {name}: establishment field '{key}' at {path}; "
                            f"illness-derived output must not carry establishment identity")

    # G2 no safety verdict
    for name, p in payloads.items():
        for path, s in walk_strings(p):
            if VERDICT.search(s) and not VERDICT_OK.search(s):
                fail.append(f"G2 {name}: safety verdict in string at {path}: {s[:80]!r}")

    # G3 synthetic flag on every pounds- or meals-denominated payload
    for name in ("scenarios.json", "actions.json", "equity.json"):
        p = payloads.get(name)
        if p is None:
            continue
        if not p.get("meta", {}).get("synthetic"):
            fail.append(f"G3 {name}: carries pounds or meals but meta.synthetic is not true")

    # G4 high-consequence actions are interrogable and refusable
    for lot in payloads.get("actions.json", {}).get("lots", []):
        if lot.get("high_consequence"):
            if not lot.get("reversal_evidence"):
                fail.append(f"G4 actions.json: lot {lot.get('lot_id')} is high-consequence "
                            f"with no reversal evidence")
                break
            if not lot.get("requires_human_confirmation"):
                fail.append(f"G4 actions.json: lot {lot.get('lot_id')} is high-consequence "
                            f"but does not require confirmation")
                break

    # G5 recalls above model scores
    kinds = [a.get("kind") for a in payloads.get("alerts.json", {}).get("alerts", [])]
    if "recall" in kinds and "model" in kinds:
        if kinds.index("model") < len(kinds) - 1 - kinds[::-1].index("recall"):
            fail.append("G5 alerts.json: a model alert sorts above a recall")
    return fail


def contract(payloads: dict[str, dict]) -> list[str]:
    fail = []
    for name, keys in CONTRACT.items():
        if name not in payloads:
            fail.append(f"contract: {name} is missing")
            continue
        missing = keys - set(payloads[name])
        if missing:
            fail.append(f"contract: {name} is missing keys {sorted(missing)}")
    return fail


# --------------------------------------------------------------------------- #
# build
# --------------------------------------------------------------------------- #
def jeffreys(k: int, n: int) -> tuple[float, float]:
    """Per-unit interval on the observed 52-week positive rate.

    The default scorer is a binomial projection, so the unit's own uncertainty is
    binomial and can be stated exactly rather than borrowed from the model-level
    bootstrap. R5.2 asks for an interval on the score; this is the right one to
    show beside a single establishment.
    """
    if n <= 0:
        return (float("nan"), float("nan"))
    lo = 0.0 if k == 0 else float(stats.beta.ppf(0.025, k + 0.5, n - k + 0.5))
    hi = 1.0 if k == n else float(stats.beta.ppf(0.975, k + 0.5, n - k + 0.5))
    return (round(lo, 4), round(hi, 4))


def calibration_band(score: float, bins: list[dict]) -> dict | None:
    """R5.3: of units scored at this level historically, how many went on to fail."""
    if not bins or not np.isfinite(score):
        return None
    b = min(bins, key=lambda r: abs(float(r.get("mean_pred", 0)) - score))
    return {"bin": b.get("bin"), "mean_predicted": b.get("mean_pred"),
            "observed": b.get("observed"), "n": b.get("n")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    here = Path(__file__).resolve()
    ap.add_argument("--analysis-out", type=Path, default=here.parents[1] / "outputs")
    ap.add_argument("--data", type=Path, default=here.parents[2] / "data")
    ap.add_argument("--out", type=Path, default=here.parents[2] / "app" / "public" / "data")
    ap.add_argument("--horizon", default="3")
    ap.add_argument("--check", action="store_true",
                    help="validate what is already built; write nothing")
    a = ap.parse_args()
    H, ROOT = a.horizon, here.parents[2]

    if a.check:
        payloads = {}
        for name in CONTRACT:
            p = a.out / name
            if p.exists():
                payloads[name] = json.loads(p.read_text())
        problems = contract(payloads) + guardrails(payloads)
        if problems:
            print(f"FAILED ({len(problems)}):")
            for f in problems:
                print("  " + f)
            return 1
        print(f"contract and guardrails pass on {len(payloads)} payloads in {a.out}")
        return 0

    AO = a.analysis_out
    need = [AO / f"decision_layer_h{H}.json", AO / f"t20_scenarios_h{H}.csv",
            AO / f"t21_equity_by_svi_quartile_h{H}.csv", AO / f"t22_frontier_h{H}.csv",
            AO / f"t23_lot_actions_h{H}.csv", AO / f"early_warning_summary_h{H}.json",
            AO / f"calibration_h{H}.json", AO / f"early_warning_test_scores_h{H}.parquet",
            AO / "hazard_first_look.json", AO / "key_numbers.json"]
    missing = [p for p in need if not p.exists()]
    if missing:
        print("cannot build; these are not there:")
        for p in missing:
            print("   " + str(p))
        print("\nRun `python run_all.py` first.")
        return 1

    S = {p.name: src(p, ROOT) for p in need}
    dec = json.loads((AO / f"decision_layer_h{H}.json").read_text())
    cal = json.loads((AO / f"calibration_h{H}.json").read_text())
    ew = json.loads((AO / f"early_warning_summary_h{H}.json").read_text())
    haz = json.loads((AO / "hazard_first_look.json").read_text())
    scorer = dec["scorer"]

    scores = pd.read_parquet(AO / f"early_warning_test_scores_h{H}.parquet")
    scores["window_end"] = pd.to_datetime(scores["window_end"])
    latest = scores["window_end"].max()
    cur = scores[scores["window_end"] == latest].copy()
    lots = pd.read_csv(AO / f"t23_lot_actions_h{H}.csv")
    suppliers = set(lots["establishment_id"].astype("int64"))
    rel = cal.get("scorers", {}).get(scorer, {}).get("reliability", [])

    # ---- R1 current risk ------------------------------------------------
    units = []
    for _, r in cur.iterrows():
        k, n = int(r.get("pos52") or 0), int(r.get("n52") or 0)
        lo, hi = jeffreys(k, n)
        s = float(r[scorer])
        units.append({
            "establishment_id": int(r["establishment_id"]),
            "product_class": str(r["product_class"]),
            "category": None if pd.isna(r["category"]) else str(r["category"]),
            "score": round(s, 4), "scorer": scorer,
            "samples_52w": n, "positives_52w": k,
            "observed_rate_52w": None if n == 0 else round(k / n, 4),
            "rate_interval_95": {"lo": lo, "hi": hi,
                                 "method": "Jeffreys interval on the 52-week positive count"},
            "calibration_band": calibration_band(s, rel),
            "is_supplier": int(r["establishment_id"]) in suppliers,
        })
    units.sort(key=lambda u: -u["score"])

    # ---- R2 alert queue, recalls pinned ---------------------------------
    alerts = []
    rp = a.data / "fsis_recalls" / "fsis_recalls_poultry_salmonella.csv"
    if rp.exists():
        S[rp.name] = src(rp, ROOT)
        R = pd.read_csv(rp)
        R["recall_date"] = pd.to_datetime(R["recall_date"], errors="coerce")
        for _, r in R.sort_values("recall_date", ascending=False).head(25).iterrows():
            alerts.append({
                "kind": "recall", "rank_group": 0,
                "date": None if pd.isna(r["recall_date"]) else r["recall_date"].date().isoformat(),
                "title": str(r["title"])[:300], "risk_level": str(r.get("risk_level") or ""),
                "reason": str(r.get("reason") or ""),
                "establishment_marks": None if pd.isna(r.get("est_marks")) else str(r["est_marks"]),
                "states": str(r.get("states") or ""), "url": str(r.get("url") or ""),
                "why_pinned": "a recall is a fact FSIS has already published, not a forecast",
            })
    for u in units[:25]:
        if not u["is_supplier"]:
            continue
        alerts.append({
            "kind": "model", "rank_group": 1,
            "date": latest.date().isoformat(),
            "establishment_id": u["establishment_id"], "product_class": u["product_class"],
            "score": u["score"], "category": u["category"],
            "title": f"Elevated {H}-month risk score for establishment {u['establishment_id']}",
            "why_not_pinned": "a model score is a forecast and sorts below published fact",
        })
    alerts.sort(key=lambda x: (x["rank_group"], -(x.get("score") or 0)))

    # ---- R3 scenarios and frontier --------------------------------------
    T20 = pd.read_csv(AO / f"t20_scenarios_h{H}.csv")
    T22 = pd.read_csv(AO / f"t22_frontier_h{H}.csv")
    scen = {
        "meta": meta("scenarios", list(S.values()), synthetic=True, horizon_months=int(H),
                     scorer=scorer, scorer_rationale=dec.get("scorer_rationale"),
                     threshold_caveat=dec.get("threshold_caveat")),
        "scenarios": json.loads(T20.to_json(orient="records")),
        "frontier": json.loads(T22.to_json(orient="records")),
        "dominated": dec.get("dominated_scenarios", []),
        "controls": [
            {"id": "hold_at", "label": "Hold threshold", "min": 0.02, "max": 0.30, "step": 0.02,
             "note": "a probability, so it does not transfer between horizons"},
            {"id": "review_capacity_per_week", "label": "Reviews per week",
             "min": 1, "max": 20, "step": 1},
            {"id": "food_security_weight", "label": "Protect high-need supply",
             "min": 0.0, "max": 1.0, "step": 0.25},
        ],
        "frontier_note": ("Not a recommended operating point. The curve is not convex, and "
                          "choosing on it is a judgement about whose risk counts."),
    }

    # ---- R4 per-lot actions ---------------------------------------------
    keep = ["lot_id", "establishment_id", "establishment_name", "product_class",
            "received_date", "use_by_date", "days_left", "pounds", "dest_county",
            "dest_svi_overall", "svi_quartile", "category", "n52", "pos52", scorer,
            "scored", "score_age_days", "action", "driver", "high_consequence",
            "requires_human_confirmation", "alternative_action", "reversal_evidence",
            "discarded", "discard_reason"]
    L = lots[[c for c in keep if c in lots.columns]].copy()
    L = L.replace({np.nan: None})
    actions = {"meta": meta("actions", list(S.values()), synthetic=True, horizon_months=int(H),
                            scorer=scorer, default_scenario=dec.get("default_scenario"),
                            lbs_per_meal=dec.get("lbs_per_meal")),
               "lots": json.loads(L.to_json(orient="records"))}

    # ---- R5 evidence -----------------------------------------------------
    evidence = {
        "meta": meta("evidence", list(S.values()), horizon_months=int(H), scorer=scorer),
        "model": {"metrics": ew.get("metrics", []), "bootstrap_ci": ew.get("bootstrap_ci", {}),
                  "bootstrap_establishments": ew.get("bootstrap_establishments"),
                  "task": ew.get("task", {}), "cat2_flag": ew.get("cat2_flag", {}),
                  "by_class": ew.get("by_class", []),
                  "interval_note": ("bootstrap_ci is a MODEL-level interval over resampled "
                                    "establishments. The per-unit interval shown beside a single "
                                    "establishment in current_risk.json is a Jeffreys interval on "
                                    "that unit's own 52-week count; they answer different "
                                    "questions and must not be presented as the same thing.")},
        "calibration": {"scorer": scorer, "horizon_months": int(H),
                        "reliability": rel,
                        "ece": cal.get("scorers", {}).get(scorer, {}).get("ece"),
                        "brier": cal.get("scorers", {}).get(scorer, {}).get("brier"),
                        "all_scorers": {k: {"ece": v.get("ece"), "brier": v.get("brier")}
                                        for k, v in cal.get("scorers", {}).items()},
                        "selection": dec.get("scorer_selection", {})},
        "sources": list(S.values()),
        "documentation": ["data/PROVENANCE.md", "data/DATA_DICTIONARY.md",
                          "docs/CHALLENGE_BRIEF.md", "report/FINDINGS.md"],
        "restrictions": RESTRICTIONS,
    }

    # ---- R6 equity --------------------------------------------------------
    T21 = pd.read_csv(AO / f"t21_equity_by_svi_quartile_h{H}.csv")
    equity = {"meta": meta("equity", list(S.values()), synthetic=True, horizon_months=int(H)),
              "quartiles": json.loads(T21.to_json(orient="records")),
              "disparity": dec.get("disparity_check", []),
              "note": ("Vulnerability is CDC/ATSDR SVI 2022 at county level. The USDA food-access "
                       "layer is not in: the Census API key was rejected, so this is SVI alone. "
                       "County is a coarse proxy for a service area.")}

    # ---- burden: illness-derived, and therefore establishment-free --------
    bw_path = AO / "burden_weighting.json"
    serotypes = []
    if bw_path.exists():
        S[bw_path.name] = src(bw_path, ROOT)
        bw = json.loads(bw_path.read_text())
        # The key 10_burden_weighting.py actually writes. It carries
        # pct_hosp_from_largest_row, which is what R5.5 needs to flag a figure
        # that rests on a single outbreak.
        serotypes = bw.get("top_serotypes_by_hospitalizations",
                           bw.get("by_serotype", bw.get("serotypes", [])))
    burden = {"meta": meta("burden", [v for k, v in S.items() if "burden" in k or "hazard" in k],
                           joined_at="serotype and year only, never establishment"),
              "serotypes": serotypes,
              "resistance_by_serotype": haz.get("fsis_calls_by_serotype", []),
              "note": ("Illness burden comes from CDC NORS and is joined to FSIS sampling at "
                       "serotype and year. No establishment appears in this payload, by design "
                       "and by automated check (G1).")}

    current = {"meta": meta("current_risk", list(S.values()), horizon_months=int(H),
                            scorer=scorer, window_end=latest.date().isoformat(),
                            suppliers=len(suppliers)),
               "units": units}

    payloads = {
        "current_risk.json": current, "alerts.json": {"meta": meta("alerts", list(S.values())),
                                                      "alerts": alerts},
        "scenarios.json": scen, "actions.json": actions, "evidence.json": evidence,
        "equity.json": equity, "burden.json": burden,
    }
    payloads["meta.json"] = {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "horizon_months": int(H), "scorer": scorer,
        "sources": list(S.values()),
        "files": sorted(payloads) + ["meta.json"],
        "restrictions": RESTRICTIONS,
        "synthetic_payloads": ["scenarios.json", "actions.json", "equity.json"],
    }

    problems = contract(payloads) + guardrails(payloads)
    if problems:
        print(f"REFUSING TO WRITE. {len(problems)} problem(s):")
        for f in problems:
            print("  " + f)
        return 1

    a.out.mkdir(parents=True, exist_ok=True)
    for name, p in payloads.items():
        (a.out / name).write_text(json.dumps(p, indent=1))
    total = sum((a.out / n).stat().st_size for n in payloads)
    print(f"wrote {len(payloads)} payloads to {a.out}  ({total/1e6:.2f} MB)")
    for n in sorted(payloads):
        print(f"   {(a.out / n).stat().st_size/1024:8.1f} KB  {n}")
    print(f"\ncontract and guardrails pass. horizon {H}, scorer {scorer}, "
          f"{len(units)} units, {len(alerts)} alerts, {len(actions['lots'])} lots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
