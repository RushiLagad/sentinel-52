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
- [x] **1.6** **Done.** `19_build_data_dictionary.py` regenerates it across all 18 built tables, not
  just the seven FSIS ones: the four outside layers, the simulated inventory, and the decision
  layer's own outputs. Three things worth keeping: it resolves the organism-prefix rename that
  `02_build_tables.py` applies, so `sal_isolates.ampicillin_mic` finds the dictionary's
  `salmonella_ampicillin_mic` rather than reading as undocumented; it distinguishes three
  provenances rather than two, since the MPI directory, the demographic file, the category workbooks
  and the cecal files carry **no FSIS dictionary of their own**, so those columns are FSIS's but the
  wording is ours and is labelled as such; and it **refuses to invent a description** — an unknown
  column is written out as UNDOCUMENTED and `--check` exits non-zero while any remain, which is what
  hook H2 relies on. Wired into `run_all.py`, so it cannot drift from the tables it documents. _(deliverable 4)_
- [x] **1.7** **Done.** `18_figure_system_map.py` draws it as `fig6_one_health_system_map.png`, in the
  same palette and pixel convention as `07_figures.py` so the figures read as one set. Three things
  the figure is responsible for: which domain each dataset belongs to, which two arrows carry the
  argument (climate into production, illness burden into population vulnerability), and the arrow we
  refuse to draw. Establishment-to-illness is drawn as a crossed dashed link with the reason on it,
  rather than being silently absent, so a reader who looks for it finds it labelled.
  _(T1, explicitly required)_
- [ ] **1.8** Write the decision statement into the README. Draft is in `requirements.md`. _(T1)_

## Phase 2: model completeness (T2, days 2-3)

- [ ] **2.1** `15_risk_model.py`: extend the existing early-warning features with climate, serotype
  burden, recall history and destination vulnerability. _(T2, R8)_
- [x] **2.2** **Done.** `05c_calibration.py` emits reliability tables and a figure for both scorers at
  horizons 3, 6 and 12. The result worth carrying into the report is that **which scorer is better
  calibrated depends on the horizon**, and an earlier version of this note got that wrong by quoting
  only h6:
  - **h6**: gradient boosting wins. ECE 0.0049 against the projection's 0.0092; GB's top decile
    predicts 0.4342 against 0.4227 observed, which is close to exact.
  - **h3**: the projection wins, and not narrowly. ECE 0.0056 against GB's 0.0213, and GB
    over-predicts its top decile badly — 0.4369 predicted against 0.3032 observed, a 44% overshoot.
  - **h12**: neither is good. Both near ECE 0.019, both over-predicting the top decile.

  The projection also emits exactly zero for 74 test rows at h6, of which 2 failed. This horizon
  dependence is what decides the scorer in 2.4 and in `16_decision_layer.py`. _(T2, R8.2)_
- [x] **2.3** **Ablation done** for the sources we currently hold: `05d_ablation.py`, leave-one-group-out
  over ten source groups, ΔAUROC and ΔAP with establishment-clustered bootstrap intervals, at horizons
  3, 6 and 12. Groups whose effect is within noise are kept in the table and labelled. **Extend `GROUPS`
  in that script when climate, recalls, SVI and food access land in Phase 1** — the table grows without
  any other change. _(T2 marginal value, T5 ablation, R8.4)_
- [x] **2.4** **Done, and the reason is calibration rather than preference for transparency.** The
  projection is the default scorer in `16_decision_layer.py`. A hold-or-divert decision acts on an
  absolute probability, not on a ranking, so calibration matters more than the AUROC gap — and at the
  3-month horizon the decision layer runs on, the projection is the better calibrated scorer by a
  factor of four (2.2). The gap to the integrated model is reported with establishment-clustered
  bootstrap intervals in `early_warning_summary_h*.json`: at h6, d_auroc_gb median +0.008
  (95% 0.000 to 0.016) and d_ap_gb median +0.003 (−0.036 to 0.041), so the integrated model's
  advantage in average precision is not distinguishable from zero. `--scorer gb` switches it for
  comparison. _(R8.1)_

## Phase 3: the decision layer (T3, days 3-4)

- [x] **3.1** **Done.** `16_decision_layer.py` maps score plus constraints to the four actions.
  Lots join to scores with a backward as-of join on `window_end <= received_date`, so a lot only
  knows what was published before it arrived; a score older than `--max-score-age-days` counts as no
  score rather than as low risk. Shelf life gates holding, and diversion goes to a cooked-meal
  channel rather than to a bin, which is the actor-specific move that makes the health-versus-loss
  tension resolvable at all. 80% of lots are scorable, median score age 19 days. _(T3, R4)_
- [x] **3.2** **Done, with one correction worth keeping.** The capacity-matched scenario derives its
  threshold from review capacity instead of carrying a hardcoded one, because a scenario called
  capacity-matched that uses 28% of capacity is mislabelled. Having fixed that, it turns out to be
  **dominated**: filling the review queue buys +0.4 points of recall for 54% more food destroyed,
  since each extra hold consumes shelf life some lots do not have. The script reports dominance
  relations rather than picking a winner — and dominance is **not horizon-robust**: at h3
  `capacity_matched` loses to `food_security_weighted`, at h6 it wins. That is a property of the
  run, so the report must name the horizon with any such claim. _(T3 three-scenario minimum, R3.3)_
- [x] **3.3** Compare every scenario against the rule-based policy (hold anything Category 2 or 3).
  _(T3 rule-based comparison, R3.4)_
- [x] **3.4** Equity objective: hold and divert rates by destination SVI quartile, reported in both
  directions. _(T3 equity objective, R6)_
- [x] **3.5** **Done.** Loss arises from two mechanical causes, both derived from the simulated shelf
  life, with no spoilage rate assumed: a review hold that leaves too little shelf life to distribute,
  and diverted pounds beyond the cooked channel's capacity. Both error types are reported in meals at
  1.2 lb/meal. "Missed risk" was renamed **exposure** — pounds distributed uncooked from plants whose
  sampling later deteriorated — because the original name implied an illness count that the FSIS
  licence forbids us to claim. _(challenge question, R7)_
- [x] **3.6** Mark hold and divert high-consequence, with the evidence that would reverse them.
  _(T3 human review, R4.4)_

## Phase 4: the app, through Kiro (T4, days 4-6)

- [x] **4.1** **Done.** `17_build_app_data.py` writes eight payloads to `app/public/data/`, each with
  a `meta` block naming every source file, its SHA-256 prefix and its modification time. The app
  computes nothing: a figure not in these files cannot appear in the interface.
  It also carries the guardrails as executable checks, and `--check` re-runs them without writing,
  which is what hooks H3 and H4 call. All five were verified by injecting a violation of each and
  confirming a non-zero exit, plus one contract break:
  G1 establishment identity in illness-derived output · G2 a safety verdict in any string ·
  G3 the synthetic flag on every pounds-denominated payload · G4 reversal evidence and human
  confirmation on every high-consequence action · G5 recalls sorted above model scores.
  The build refuses to write at all if any check fails. _(R9, guardrail)_
- [x] **4.2** Scaffold React + Vite, `base: '/sentinel-52/'`, hash routing. _(T4)_
  **Done.** React 18 + Vite 5, `base: '/sentinel-52/'`, hash routing with the active section tracked by IntersectionObserver. Builds in ~1s to 175 kB of JS.
- [x] **4.3** `CurrentRiskView` _(R1)_
  **Done.** Sortable, filterable, with the Jeffreys interval and the calibration band per row; clicking a row filters the action panel to that plant.
- [x] **4.4** `AlertQueue`, recalls pinned above model scores _(R2)_
  **Done.** Published recalls pinned in rank group 0 above model items, with the recovered establishment marks and the caveat that marks are recoverable for only about a third of notices.
- [x] **4.5** `ScenarioBuilder` with the trade-off frontier _(R3)_
  **Done.** Threshold slider snaps to the precomputed sweep; SVG frontier with the two error types in shared units; four scenario cards with dominance called out and `NOT EXECUTABLE` where holds exceed capacity. Capacity and the food-security weight vary through the named scenarios and the page says so.
- [x] **4.6** `RecommendedActionPanel` with counterfactual and cost _(R4)_
  **Done.** Driver, cost in pounds and community, the opposite action with its cost, reversal evidence, and the discard reason where the lot is lost.
- [x] **4.7** `EvidencePanel` with interval, calibration and sources _(R5)_
  **Done.** Metrics with bootstrap intervals, reliability diagram on a log scale, scorer-selection reason, burden by serotype with the single-outbreak flag at 80%, FSIS WGS resistance, every source with its hash, and the restriction in full.
- [x] **4.8** `EquityView` _(R6)_
  **Done.** Quartile table for the selected scenario, disparity stated in both directions, and a visible notice rather than a footnote when it runs against high-need counties.
- [x] **4.9** `ConfirmHighConsequence` blocking dialog _(R4.4)_
  **Done.** Blocking dialog on hold and divert. Confirming records an acknowledgement in the page and executes nothing, and the dialog says so.
- [x] **4.10** `SyntheticBadge` on every pounds-denominated figure _(design: honest inventory)_
  **Done.** `SyntheticBadge` beside every pounds or meals figure; which payloads are simulated is read from `meta.json`, not hardcoded, and the render test fails if a card with lb or meals lacks the badge.
- [x] **4.11** Palette through the dataviz validator, light and dark _(R10)_
  **Done.** Blue, orange, violet, green — all six validator checks pass in light and dark. Orange and green deliberately non-adjacent. Gray never a series.
- [x] **4.12** Guardrail tests: no establishment-illness join, no "safe"/"unsafe" verdict, synthetic
  flags present, confirmation unskippable _(design: testing)_
  **Done.** 17 vitest tests: G1–G4 against the shipped JSON, the data contract, and the rendered UI (no verdict words outside the restriction, badge coverage, the dialog executes nothing).
- [x] **4.13** Move `docs/pages-workflow-for-later.yml` into `.github/workflows/` **only after**
  `npm run build` succeeds locally, and set Pages source to GitHub Actions. _(deliverable 3)_
  **Done.** `npm run build` succeeds; workflow moved to `.github/workflows/deploy-pages.yml`. **Rushi: Settings → Pages → Source → GitHub Actions**, once.

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

- [x] **H1** **Done.** `.kiro/hooks/h1-validate-category-rebuild.json`.
- [x] **H2** **Done.** `.kiro/hooks/h2-regenerate-data-dictionary.json`, an agent hook rather than
  a command: deciding whether an edit actually changed a schema, and describing a new column
  honestly, is not something a script can do.
- [x] **H3** **Done.** `.kiro/hooks/h3-app-data-contract.json`.
- [x] **H4** **Done.** `.kiro/hooks/h4-decision-layer-guardrails.json`. Kiro has no git-commit
  trigger, so it fires on edit instead, which is strictly earlier and therefore safer. All four
  matchers were tested against eleven real paths to confirm each fires on what it should and on
  nothing else. **Open Kiro's hooks panel and confirm all four load before relying on them** — a
  hook that fails to load fails silently, which is the class of problem these exist to prevent.

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
- **(manual)** `analysis/scripts/11_fetch_noaa.py` — NOAA climate layer. Written by hand. The first
  version used the daily-summaries endpoint and silently truncated at exactly 60,000 records per
  state, which was caught only from repeated round numbers in the output; it was rewritten to a
  bounded, deterministically chosen station panel on GSOM monthly data.
- **(manual)** `analysis/scripts/13_fetch_vulnerability.py` — CDC/ATSDR SVI and Census ACS. Written
  by hand because both endpoints had to be probed live: the SVI CSV layout and the Census API's
  habit of returning an HTML error page rather than JSON for a bad key.
- **(manual)** `analysis/scripts/14_build_synthetic_inventory.py` — seeded synthetic lot generator.
  Written by hand.
- **(manual)** `analysis/scripts/17_build_app_data.py` and `.kiro/hooks/*.json` — the app data
  contract, the five guardrails and the four hooks. Written by hand on 2026-10-27, by an explicit
  team decision to hand-build Phase 4 rather than drive it through Kiro, given the time remaining.
  Recorded here because the alternative was to leave the reader to infer it.
- **(manual)** `analysis/scripts/16_decision_layer.py` — the decision layer. Written by hand over
  several rounds of correction, each prompted by reading the output rather than the code: the first
  version gave holding no cost at all, which made a conservative policy look free; the second
  hardcoded a capacity-matched threshold that used 28% of capacity; the third hardcoded the scorer
  and was then run by `run_all.py` at the one horizon where that scorer is the worse calibrated.
- **(manual)** `analysis/run_all.py` — repeatedly, as scripts were added.
- **(manual)** `analysis/scripts/12_fetch_fsis_recalls.py` — FSIS recall fetcher. Written by hand
  because the endpoint, field schema and establishment-mark format had to be probed against the live
  API first, and the mark-extraction regex was validated against observed strings before the script
  was written. The regex self-test cases in that session are reproduced as assertions in the
  docstring's limitation note.
