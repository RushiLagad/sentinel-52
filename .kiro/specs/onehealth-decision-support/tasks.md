# Tasks: Sentinel-52 One Health decision support

Deadline **2026-11-02 16:00 US Central**. No push after that time, on pain of disqualification.
Seven days from 2026-10-26.

Each task names the brief task it satisfies (T1-T5) and the spec requirement (R1-R10). Tick items off
here as they land. Record substantial manual edits to Kiro-generated code in the log at the bottom,
because the brief asks for that disclosure explicitly.

`[ ]` not started · `[~]` in progress · `[x]` done · **(manual)** hand-written, with reason

---

## Priority order, and why

The gaps are not equal. Ranked by marks at risk against effort:

1. **Required data we do not have** (climate, recalls, vulnerability, food access). Without these,
   One Health integration (20%) has nothing to integrate and Task 1 is incomplete.
2. **The decision layer** (actions, scenarios, equity, loss). Operational decision support is 25% and
   currently we have a watch list, which is not a decision.
3. **Calibration and ablation.** Named requirements inside the 25% rigor criterion, and cheap given
   the pipeline already exists.
4. **The app.** 15%, but it is also where the other three become visible to a judge.
5. **Report and team science.** 15%, and the report is the team's own writing, not Kiro's.

---

## Phase 1: close the data gaps (T1, days 1-2)

- [x] **1.1** **Done.** `11_fetch_noaa.py` against NOAA/NCEI CDO, dataset GSOM (monthly, not daily).
  Token from `NOAA_CDO_TOKEN`, never committed. Per state it selects the 8 best-covered stations whose
  record spans the window, deterministically, and averages them; the panel is listed in
  `noaa_stations_used.csv`. Result: 7,644 state-months across 49 places, no failed fetches.
  Caveat in PROVENANCE: Delaware has only 2 stations despite being 2.3% of routine sampling.
  _(T1, brief-required)_
- [x] **1.2** **Done.** `12_fetch_fsis_recalls.py` against `fsis.usda.gov/fsis/api/recall/v/1`, no key
  needed. Emits all recalls and a poultry-or-Salmonella subset, with risk level, class, reason,
  outbreak flag and states. **Run it to populate `data/fsis_recalls/`** — the container this was
  written in cannot reach fsis.usda.gov, so the cache is not committed yet.
  Known limitation, documented in PROVENANCE: `field_establishment` is a company name, not an
  establishment number. Numbers come from USDA marks in the product text and are recoverable for only
  36.6 percent of relevant recalls (206 of 563). _(T1, brief-required)_
- [ ] **1.3** `13_fetch_vulnerability.py`. CDC/ATSDR SVI by county, and USDA food-access measures.
  Both public, both documented. _(T1, team-added, satisfies the vulnerability and food-security
  requirement)_
- [x] **1.4** **Done.** `14_build_synthetic_inventory.py`, deterministic given `--seed`. Actor is a
  regional Arkansas food bank. Supplier panel is stratified **per product class** so all five FSIS
  standards appear; taking the top plants overall gave an almost pure chicken panel and left turkey
  untestable. Output: ~1,880 lots, every row `is_synthetic = True`, assumptions and distortions in
  `data/inventory/ASSUMPTIONS.json` and PROVENANCE section 10.
  The panel joins to 101 real establishment-by-product postings, 18 of them Category 3, so the
  decision layer acts on real risk signal. _(T1)_
- [ ] **1.5** Extend `data/PROVENANCE.md` with all four, including the synthetic generator's
  assumptions stated as assumptions. _(T1, deliverable 4)_
- [ ] **1.6** Regenerate `data/DATA_DICTIONARY.md`. _(deliverable 4)_
- [ ] **1.7** Draw the One Health system map as a figure for the report. Structure is in `design.md`.
  _(T1, explicitly required)_
- [ ] **1.8** Write the decision statement into the README. Draft is in `requirements.md`. _(T1)_

## Phase 2: model completeness (T2, days 2-3)

- [ ] **2.1** `15_risk_model.py`: extend the existing early-warning features with climate, serotype
  burden, recall history and destination vulnerability. _(T2, R8)_
- [x] **2.2** **Done.** `05c_calibration.py` emits reliability tables and a figure for both scorers at
  horizons 3, 6 and 12. Result worth carrying into the report: the projection is the **worse**
  calibrated of the two (ECE 0.0092 against 0.0045), under-stating risk across the lower deciles and
  over-stating it at the top, and it emits exactly zero for 74 test rows of which 2 failed.
  _(T2, R8.2)_
- [x] **2.3** **Ablation done** for the sources we currently hold: `05d_ablation.py`, leave-one-group-out
  over ten source groups, ΔAUROC and ΔAP with establishment-clustered bootstrap intervals, at horizons
  3, 6 and 12. Groups whose effect is within noise are kept in the table and labelled. **Extend `GROUPS`
  in that script when climate, recalls, SVI and food access land in Phase 1** — the table grows without
  any other change. _(T2 marginal value, T5 ablation, R8.4)_
- [ ] **2.4** Confirm the transparent projection stays the default scorer and the gap to the
  integrated model is reported with both intervals. _(R8.1)_

## Phase 3: the decision layer (T3, days 3-4)

- [ ] **3.1** `16_decision_layer.py`: map score plus constraints to the four actions. _(T3, R4)_
- [ ] **3.2** Implement the three named scenarios: conservative, capacity-matched,
  food-security weighted. _(T3 three-scenario minimum, R3.3)_
- [ ] **3.3** Compare every scenario against the rule-based policy (hold anything Category 2 or 3).
  _(T3 rule-based comparison, R3.4)_
- [ ] **3.4** Equity objective: hold and divert rates by destination SVI quartile, reported in both
  directions. _(T3 equity objective, R6)_
- [ ] **3.5** Food loss: pounds held, diverted, discarded, and avoidable loss from false alarms,
  expressed in the same units as missed risk where possible. _(challenge question, R7)_
- [ ] **3.6** Mark hold and divert high-consequence, with the evidence that would reverse them.
  _(T3 human review, R4.4)_

## Phase 4: the app, through Kiro (T4, days 4-6)

- [ ] **4.1** `17_build_app_data.py` -> `app/public/data/*.json`, each with a `meta` block naming
  source files and generation time. Assert no establishment identifier appears in any illness-joined
  output, and fail the build if one does. _(R9, guardrail)_
- [ ] **4.2** Scaffold React + Vite, `base: '/sentinel-52/'`, hash routing. _(T4)_
- [ ] **4.3** `CurrentRiskView` _(R1)_
- [ ] **4.4** `AlertQueue`, recalls pinned above model scores _(R2)_
- [ ] **4.5** `ScenarioBuilder` with the trade-off frontier _(R3)_
- [ ] **4.6** `RecommendedActionPanel` with counterfactual and cost _(R4)_
- [ ] **4.7** `EvidencePanel` with interval, calibration and sources _(R5)_
- [ ] **4.8** `EquityView` _(R6)_
- [ ] **4.9** `ConfirmHighConsequence` blocking dialog _(R4.4)_
- [ ] **4.10** `SyntheticBadge` on every pounds-denominated figure _(design: honest inventory)_
- [ ] **4.11** Palette through the dataviz validator, light and dark _(R10)_
- [ ] **4.12** Guardrail tests: no establishment-illness join, no "safe"/"unsafe" verdict, synthetic
  flags present, confirmation unskippable _(design: testing)_
- [ ] **4.13** Move `docs/pages-workflow-for-later.yml` into `.github/workflows/` **only after**
  `npm run build` succeeds locally, and set Pages source to GitHub Actions. _(deliverable 3)_

## Phase 5: report and team science (T5, days 6-7)

The report is the team's own writing. Kiro and Claude generate code, figures and tables; the narrative
is ours.

- [ ] **5.1** Document roles across the three of us. _(T5)_
- [ ] **5.2** Record a **decision changed by another discipline** as it happens, not retrofitted.
  Capture it in the moment or it will be invented later, which would be dishonest. _(T5)_
- [ ] **5.3** Name the next dataset or partner we would add. _(T5)_
- [ ] **5.4** Answer the ten report questions in `docs/CHALLENGE_BRIEF.md`. _(deliverable 5)_
- [ ] **5.5** Limitations section: synthetic inventory, NORS outbreak-only bias, no establishment-level
  illness attribution, public NORS ending 2023 against FSIS running to FY2026. _(deliverable 5)_
- [ ] **5.6** Final README pass: judges must reproduce everything from it alone. _(deliverable 6)_
- [ ] **5.7** Verify the original Google Doc against `docs/CHALLENGE_BRIEF.md` line by line. That file
  is a summary, not the organizers' words. _(correctness)_

---

## Hooks to configure

Graded artifacts under deliverable 2.

- [ ] **H1** On edit of `analysis/scripts/fsis_categories.py`, run `04_validate_categories.py`.
- [ ] **H2** On schema change in any build script, regenerate `data/DATA_DICTIONARY.md`.
- [ ] **H3** On edit of any `analysis/scripts/*.py`, re-run the app-data contract test.
- [ ] **H4** On any commit touching the decision layer, run the guardrail tests from 4.12.

---

## Manual-change log

Written by hand before Kiro joined the project, disclosed for completeness: `analysis/scripts/01`
through `10`, `data/PROVENANCE.md`, `data/DATA_DICTIONARY.md`, `docs/CHALLENGE_BRIEF.md`, the
superseded `.kiro/specs/watchlist-app/` spec, and this spec.

Everything from Phase 1 onward is intended to be built through Kiro from this spec. Entries below as
`**(manual)** <file> — <what and why>`.

- **(manual)** `analysis/scripts/05c_calibration.py` — reliability tables and figure. Written by hand
  on 2026-10-26, before Kiro was set up on this machine.
- **(manual)** `analysis/scripts/05d_ablation.py` — leave-one-group-out ablation. Same reason.
- **(manual)** `analysis/scripts/12_fetch_fsis_recalls.py` — FSIS recall fetcher. Written by hand
  because the endpoint, field schema and establishment-mark format had to be probed against the live
  API first, and the mark-extraction regex was validated against observed strings before the script
  was written. The regex self-test cases in that session are reproduced as assertions in the
  docstring's limitation note.
