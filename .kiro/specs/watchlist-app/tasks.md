# Tasks: Sentinel-52 watch-list application

Worked top to bottom. Each task names the requirements it satisfies. Tick items off in this file as
they land, and record any place where Kiro's output was substantially rewritten by hand, because
submission item 2 asks for that disclosure explicitly.

## Status key

- `[ ]` not started · `[~]` in progress · `[x]` done
- **(manual)** marks work done by hand rather than generated, with a note on why

---

## Phase 1: data contract

- [ ] **1.1** Write `analysis/scripts/11_build_app_data.py`, emitting the files in the design's data
  contract table into `app/public/data/`. Every file carries a `meta` block with `generated_at`,
  `source_files` and `pipeline_commit`. _(R6.1, R6.2)_
- [ ] **1.2** Build `watchlist.json` from the latest posted window joined to the trailing 52-week
  counts and the projection score. One row per establishment and product-class unit. _(R1.1, R1.2)_
- [ ] **1.3** Add consecutive-months-on-list to each row by replaying the score over prior windows.
  _(R1.3)_
- [ ] **1.4** Emit `scenario.json`: the three measured operating points plus the precision/recall
  curve across list size, with measured points flagged apart from interpolated ones. _(R2.3, R2.6)_
- [ ] **1.5** Emit `leadtime.json` and `context.json` from the existing summaries. _(R3, R5)_
- [ ] **1.6** Emit `burden.json` from `burden_weighting.json`, carrying
  `pct_hosp_from_largest_row` per serotype. _(R9.1, R9.4)_
- [ ] **1.7** Emit `caveats.json` including the inferred rounding rule, the 99.75 percent validation
  result, the FSIS use restriction, and the NORS attribution gap. _(R6.4, R6.5, R9.7)_
- [ ] **1.8** Assert in the build script that no burden-derived file contains an establishment
  column. Fail the build if one appears. _(R9.8)_

## Phase 2: application shell

- [ ] **2.1** Scaffold React + Vite in `app/`, `base: '/sentinel-52/'`, hash routing. _(R7.1, R7.3)_
- [ ] **2.2** `DataProvider` with per-file load state and a named error for each failed fetch.
  _(R7.4)_
- [ ] **2.3** Layout, navigation, dark-mode toggle, footer linking `PROVENANCE.md` and
  `DATA_DICTIONARY.md`. _(R6.3, R8.4)_
- [ ] **2.4** `Chart` wrapper enforcing one y-axis, a legend at two or more series, and a paired
  `TableView`. _(R8.1, R8.2, R8.3)_
- [ ] **2.5** Run the palette through the dataviz validator for light and dark surfaces. Fix any
  FAIL before any chart ships. _(R8.1, R8.4)_

## Phase 3: the screens

- [ ] **3.1** Watch-list table: sortable, filterable, searchable, with the evidence columns visible
  so a user can see why a unit ranks where it does. _(R1.1, R1.2, R1.4, R1.5)_
- [ ] **3.2** Separate and label already-Category-3 units as current failures, not predictions.
  _(R1.6)_
- [ ] **3.3** `BudgetControl`, shared state with the scenario screen, driving list length live.
  _(R2.1, R2.2)_
- [ ] **3.4** Scenario screen: operating-point cards against the Category 2 status quo, plus the
  precision/recall curve, everything shown in units per month as well as percentages.
  _(R2.3, R2.4, R2.5)_
- [ ] **3.5** Lead-time screen with denominators and the unrated-entry disclosure on the page.
  _(R3.1, R3.2, R3.3)_
- [ ] **3.6** Establishment detail with history, position against the standard, and an explicit
  serotype empty state. _(R4.1, R4.2, R4.3, R4.4)_
- [ ] **3.7** Context screen: FSIS indicator against target, Category 3 by size, the Infantis shift.
  _(R5.1, R5.2, R5.3, R5.4)_
- [ ] **3.8** Burden screen: prevalence against burden per serotype, the chicken and turkey policy
  comparison, single-outbreak flags on anything above 80 percent. _(R9.1, R9.4, R9.5, R9.6)_
- [ ] **3.9** Burden-weighted ordering toggle on the watch list, showing which units move and why.
  _(R9.2, R9.3)_
- [ ] **3.10** Methods screen carrying every caveat. _(R6.4, R6.5, R9.7)_

## Phase 4: correctness

- [ ] **4.1** Contract test: every `app/public/data/*.json` has the keys its components read. This is
  the test that catches a pipeline change silently breaking the app. _(R6.1)_
- [ ] **4.2** Unit tests for ranking order, budget-to-count arithmetic, filter composition, and the
  share-to-units-per-month formatter. _(R1.1, R2.2)_
- [ ] **4.3** Render test per page against committed fixture data. _(R7.4)_
- [ ] **4.4** Accessibility check: contrast, and a table view present for every chart.
  _(R8.1, R8.2)_
- [ ] **4.5** Check the layout at 390 pixels wide. _(R7.5)_

## Phase 5: ship

- [ ] **5.1** Fill in `app/README.md` with real build, run and deploy instructions. _(submission item 6)_
- [ ] **5.2** Move `docs/pages-workflow-for-later.yml` to `.github/workflows/deploy-pages.yml` and
  set Settings > Pages > Source to GitHub Actions. Only once `npm run build` succeeds locally, since
  a Pages workflow with nothing to build fails on every push. _(R7.1)_
- [ ] **5.3** Verify the deployed URL serves from the repository subpath without a blank page.
  _(R7.3)_
- [ ] **5.4** Record in this file every substantial manual change to Kiro-generated code.
  _(submission item 2)_

---

## Hooks to configure

Submission item 2 lists hooks as a graded artifact, so these belong in `.kiro/hooks/`:

- [ ] **H1** On edit of `analysis/scripts/fsis_categories.py`, run `04_validate_categories.py`. That
  module is load-bearing and breaking it silently would invalidate everything downstream.
- [ ] **H2** On schema change in a build script, regenerate `data/DATA_DICTIONARY.md`.
- [ ] **H3** On edit of any `analysis/scripts/*.py`, re-run the app-data contract test, so a pipeline
  change that breaks the application surfaces immediately rather than at deploy time.

## Manual-change log

Nothing yet. Entries go here as `**(manual)** <file>: <what and why>`.

Already written by hand before Kiro came into the project, and disclosed for completeness: the whole
of `analysis/scripts/01` through `10`, `data/PROVENANCE.md`, `data/DATA_DICTIONARY.md`, and this spec.
The application in `app/` is the part to be built through Kiro from this spec.
