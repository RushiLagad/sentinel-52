# Report scaffold: the ten questions, with their evidence

**The prose in the PDF is written by the team.** This file is not draft text. It is, for each
question the brief requires, what the question asks, where the evidence is, and the one or two
figures that answer it, so that writing starts from the evidence rather than from a blank page.
Every number here is in `FINDINGS.md`, `analysis/outputs/key_numbers.json` or the named table, and
each has been reproduced on two machines.

Required coverage from the brief: *methods, metrics, figures, scenarios, limitations, team science
statement*, and the ten questions below. Grading: 25% rigor · 25% operational relevance · 20% One
Health · 15% Kiro · 15% team science.

**Before any of this is written: task 5.7.** `docs/CHALLENGE_BRIEF.md` is a summary of Pedro's doc,
not verbatim. Someone reads the original against it line by line first.

---

## Q1. The decision-maker and the decision horizon

**Evidence:** README "The decision this tool supports"; `requirements.md` §Decision statement;
`fig6_one_health_system_map.png`.

- Actor: a regional Arkansas food bank. Why: the brief's three secondary objectives (availability,
  food security, avoidable loss) are its mission, not side constraints, and they collide daily with
  protecting health.
- Decision: per lot, within its perishability window. Distribute now, prioritize, hold for review,
  or divert to the cooked-meal channel.
- Horizon: 3 months. Two reasons, in `FINDINGS.md` Finding 4: the perishability window is short, and
  80% of lots have a usable score at h3 against 64% at h6, so h3 wins on recall and on food loss
  simultaneously.
- Mechanism: the USDA mark of inspection carries the establishment number.

## Q2. The role of each core dataset

**Evidence:** `data/PROVENANCE.md` §1–6; `fig6`; `key_numbers.json` → `data`.

- FSIS raw poultry sampling, FY2014–26: 325,123 samples, 37,685 Salmonella positives, 1,409
  establishments ever sampled. The backbone: scores, categories, outcomes.
- FSIS Salmonella categories: the status-quo signal and the validation target. Rebuild agrees with
  three postings on 99.75% of 2,764 rows, zero false Category 3.
- NARMS cecal: resistance context.
- CDC NORS (public endpoint, not the organisers' restricted file): human burden, joined at serotype
  × year only.
- Establishment directory and demographics: the join from mark to plant, and HACCP size.

## Q3. The added datasets and their impact

**Evidence:** `PROVENANCE.md` §7–11; `t19_ablation_h6.csv`; Finding 2; Finding 4.

- Added: NOAA GSOM climate (§9), FSIS recalls (§8), CDC/ATSDR SVI (§10), and the simulated
  inventory (§11, labelled).
- Impact on the *risk model*: none distinguishable from noise at h6. Only sampling history, the
  projection, and all-beyond-core-together move AUROC. **Say this directly; it is the result,
  and it is the reason 2.1 was reframed.**
- Impact on the *decision*: this is where they matter. SVI drives the equity check and the
  food-security scenario; recalls are pinned above forecasts in the alert queue; the inventory is
  what makes a decision exist at all.
- Not landed: USDA food access (Census key rejected). State it.

## Q4. The modeled outcome

**Evidence:** `05_early_warning_baseline.py` docstring; `evidence.json` → `model.task`.

- Unit: plant × product class × 52-week window. Outcome: entry into FSIS Category 3 within the
  horizon. Strict time split, train through 2022-09, test 2024-01 onward. h3 test set: 17,343
  unit-months, 644 new failures, base rate 3.71%.
- Scorers: binomial projection (transparent baseline) against logistic and gradient boosting.
- Scorer choice is by measured calibration at the horizon, not AUROC: projection ECE 0.0056 vs GB
  0.0213 at h3. (At h6 the order flips: 0.0092 vs 0.0049. Name the horizon on every claim.)

## Q5. Performance against the baseline

**Evidence:** `early_warning_summary_h3.json`, `h6`; `watchlist_comparison_h6.json`; Finding 2.

- Rule-based baseline (Category 2 flag), full panel, h3: recall 0.915, precision 0.145, flags 23.5%
  of units. At h6: recall 0.813, precision 0.219.
- Projection vs GB, h6: AUROC 0.917 vs 0.925; ΔAUROC median +0.008 (95% CI 0.000–0.016); ΔAP +0.003
  (−0.036 to 0.041), which is **not distinguishable from zero**. Establishment-clustered bootstrap, 578
  plants resampled whole.
- Equal-size comparison: a projection list the size of the Category 2 list reaches recall 87.7% vs
  81.3% at the same precision.
- Lead time, h6: 86% of new Category 3 entries were on the top-10% list a month before, 62.6% three
  months before.

## Q6. Which errors are costly: false alarms against missed risk

**Evidence:** Finding 4; `t20_scenarios_h3.csv`; `t22_frontier_h3.csv`; the Scenarios section of
the app.

- Both error types in the same unit, meals at 1.2 lb/meal. Avoidable loss = meals destroyed from
  plants that did not deteriorate. Exposure = meals distributed uncooked from plants that did.
  **Exposure is not an illness count; say so every time it appears.**
- The status quo: recall 1.000 on this supply base, 13.4 reviews/week against capacity 6, 108,499
  meals destroyed, 91% from plants that never deteriorated. Conservative threshold: 40% of the
  risk for 30,529 meals.
- The frontier is not convex (61,095 → 8,861 → 12,566 meals). No clean optimum; the choice is a
  value judgement about whose risk counts, and the tool declines to make it.
- All poundage is simulated. Say it in this section, not only in Limitations.

## Q7. Where food safety and food security conflict

**Evidence:** `t21_equity_by_svi_quartile_h3.csv`; `equity.json` → `disparity`; the Equity section.

- Disparity check, withheld share most- minus least-vulnerable quartile: rule-based −0.28,
  conservative −1.96, capacity-matched −0.34, food-security-weighted −2.66 points.
- Food-security weighting cuts loss by 4,971 meals at identical recall, but only because the
  protected destinations are not fed by the riskiest plants here. Where they overlap, the trade is
  real. The tool shows the gap; it does not optimise it away (R6.5).
- Divert means the cooked channel, not the bin. It is the move specific to this actor that makes the conflict
  resolvable at all. This belongs in this section.

## Q8. An end-to-end scenario

**Evidence:** `t23_lot_actions_h3.csv`; the Actions section and the confirmation dialog.

Pick one real lot from `t23` (the app's Actions section lists the 311 high-consequence ones). Walk
it: the pallet arrives → mark gives the plant → the plant's 52-week history and score → the action
and its driver → the cost in pounds and the community → the opposite action and its cost → the
evidence that would reverse it → a human confirms, and nothing executes. A diverted lot from a
Category 2 plant with 124 days of shelf life makes a clean example; a held fresh lot that spoils in
review makes the loss mechanism concrete.

## Q9. The effect of team science on the work

**Evidence:** task 5.1 (roles) and 5.2 (a decision changed by another discipline), which are open.

Two institutions, three disciplines. **5.2 has to be recorded as it happened, not reconstructed.**
If a decision was changed by someone else's discipline (the actor choice, the cooked-channel
framing, the serotype-only join, the h3 pin), write down who raised it and what changed. If nobody
wrote it down yet, do that today.

## Q10. What the tool can and can never claim, and what deployment would require

**Evidence:** `FINDINGS.md` "What this does NOT support" on every finding; the restrictions block in
`meta.json`; `PROVENANCE.md` §11.

Can claim: which plants are on a deteriorating sampling trajectory, how far ahead, how well
calibrated the number is, and what each policy costs in shared units.

Can never claim: that any food, lot or plant is safe or unsafe; any link between a plant and an
illness (FSIS licence); any real poundage (simulated); any illness count from "exposure".

Deployment would require: real inventory with lot-level provenance; a cooked-channel partner with
stated capacity; USDA food-access data and a sub-county service-area map; a review workflow where
confirmation does something; and FSIS data fresher than the quarterly posting lag.

---

## Limitations (task 5.5): the list, for the team to write up

All documented already; this is where each lives.

1. Inventory is simulated (§11). Every pounds and meals figure rests on it.
2. NORS is outbreak-only and under-attributes; burden figures can rest on a single event
   (`pct_hosp_from_largest_row`, flagged above 80%).
3. No establishment-level illness link, by licence and by design of the code.
4. Food access not in; SVI alone, county-level, static, relative (§10).
5. The h3 ablation verdicts are unstable between builds; only h6 is quoted.
6. Thresholds are horizon-specific; dominance flips between h3 and h6.
7. Decision-layer metrics are a policy's performance on 52 plants, not the model's on 578.
8. The aminoglycoside gene heuristic agrees with FSIS WGS on only 62.3%; published MDR figures use
   FSIS calls.
9. Recall marks are recoverable for 36.6% of relevant notices.
10. The inferred category rounding rule; the 2026 establishment snapshot applied to earlier years;
    enumeration absent after 2026-04-28 and for turkey carcasses; the publication lag.
11. The FSIS CDN now refuses automated download; reproduction is manual + hash check.

## Next dataset or partner (task 5.3): candidates, team decides

- **USDA Food Access Research Atlas**: the half of R6.1 that did not land. Lowest effort, highest
  relevance to the equity objective.
- **A real food bank's receiving log**, under agreement: replaces §11 and makes every pounds figure
  a measurement. Changes the project's category.
- **FSIS noncompliance records (NRs) by establishment**: a leading indicator the sampling data does
  not carry. Public via FOIA, not an API.

## AI assistance disclosure (for the PDF)

Kiro did not generate code in this repository; the `.kiro/` artifacts are in its format and were
loaded in it. Claude (Anthropic): the analysis pipeline from 2026-10-09, scripts 09 to 19, the
specs, steering and hooks, `17_build_app_data.py`, and the React UI and its tests. The
manual-change log in `tasks.md` has every file with a date and reason. The report prose is the
team's, except where the header of `REPORT.md` says otherwise.
