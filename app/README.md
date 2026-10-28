# Sentinel-52: the application

A static React site that shows a regional food bank what the analysis found about the plants it
buys from, and what each policy choice costs. It computes nothing and holds no opinions: every
number on screen is produced by the same scripts that produced the report and shipped as JSON
under `public/data/`. If a figure is not in those files, the app cannot display it.

## Build, run, test

```bash
cd app
npm install
npm run dev        # local, with hot reload
npm run build      # production build into app/dist
npm run test       # 17 tests: the four guardrails against the data, and the rendered UI
npm run check      # the Python contract check, same guardrails, on the built data
```

Requires Node 22.12 or newer (the test tooling's floor; the Pages workflow uses 22). The data files are built by
`python analysis/scripts/17_build_app_data.py --out app/public/data` after `run_all.py`; they are
committed, so the app builds on a clean clone without running the pipeline.

## Deploy

Pushing to `main` runs `.github/workflows/deploy-pages.yml`, which builds `app/` and publishes
`app/dist` to GitHub Pages. One-time setup in the repository: **Settings → Pages → Source →
GitHub Actions**. `vite.config.js` sets `base: '/sentinel-52/'` to match the Pages path, and the
app uses hash routing (`#/risk`, `#/scenarios`, …) so deep links survive a static host.

## What is on the page, and which requirement each part answers

Everything is one page with seven sections. The first is the one the tool exists for; the other six are the evidence behind it. The requirement numbers refer to
`.kiro/specs/onehealth-decision-support/requirements.md`.

| Section | Component | Requirement | What it shows |
|---|---|---|---|
| Receiving desk | `ReceivingDesk` | R4, R5 | The landing view. A lot is in front of you: the call in large type, the one-sentence reason, the plant's score, category and 52-week counts, the calibration band, what the lot weighs and whom it feeds, the opposite action with its cost, and what would reverse the call. Acknowledge, and the next lot needing a decision comes up. Works a queue; executes nothing. |
| Current risk | `CurrentRiskView` | R1 | Every plant-and-product unit with its score, FSIS category, 52-week rate with a Jeffreys interval, and the calibration band it falls in ("of units scored like this, X% went on to elevated risk"). Click a row to filter the actions below to that plant. |
| Alerts | `AlertQueue` | R2 | Recalls and public health alerts FSIS has already published, pinned above anything the model produces, because a published recall is a fact and a score is a forecast. |
| Scenarios | `ScenarioBuilder` + `Frontier` | R3 | The hold-threshold slider over the precomputed sweep, the frontier between avoidable loss and exposure in shared units (meals), and the four named scenarios with their dominance relations. Review capacity and the food-security weight vary through the named scenarios, which is where they were precomputed. |
| Actions | `RecommendedActionPanel` + `ConfirmHighConsequence` | R4 | One action per lot, the driving signal, the cost in pounds and the community served, the opposite action with its cost, and, for hold and divert, a blocking dialog carrying the evidence that would reverse it. |
| Equity | `EquityView` | R6 | Distribution and withholding by destination SVI quartile for the selected scenario, with the disparity stated whichever way it comes out. |
| Evidence | `EvidencePanel` + `Reliability` | R5 | Model metrics with establishment-clustered bootstrap intervals, the reliability diagram, why this scorer, illness burden by serotype with a flag on anything resting on a single outbreak, FSIS WGS resistance, and every source file with its hash. |

`SyntheticBadge` sits beside every pounds- or meals-denominated figure. Which payloads are
simulated is declared by the build in `meta.json`; the app reads that rather than deciding.

## Guardrails

Enforced twice: in Python when the data is built, and in `tests/` against the files the app ships.

- **G1** No establishment identifier in any illness-derived payload.
- **G2** No safety verdict anywhere. The only sentence allowed to contain the words is the
  restriction that says we never use them.
- **G3** Every pounds- or meals-denominated payload carries `synthetic: true` and is declared in
  `meta.json`.
- **G4** Every high-consequence recommendation carries reversal evidence, requires human
  confirmation, and offers the opposite action. Hold and divert are exactly the high-consequence
  set.

Nothing in the app executes an action. Confirming in the dialog records that a person has read the
recommendation and does nothing else.

## Palette

Validated 2026-10-28 with the dataviz validator, light and dark, all six checks passing in both:
lightness band, chroma floor, CVD separation (worst adjacent pair ΔE 17.1 deutan), normal-vision
floor, and contrast against the surface. Categorical order is fixed (blue, orange, violet, green),
and orange and green are deliberately non-adjacent so red-green colour vision can tell neighbours
apart. Gray is de-emphasis only and never carries a series. Colour never carries meaning alone:
every action badge carries its name in text.

## Provenance of this code

None of this code was generated by Kiro. The `.kiro/` artifacts (specs, steering, hooks) are in
Kiro's format and were loaded in Kiro, but they, `17_build_app_data.py`, the React UI in `src/` and
the tests in `tests/` were all written with Claude (Anthropic) between 2026-10-26 and 2026-10-28.
The team decided to hand-build Phase 4 given the time remaining, and recorded that decision, with
dates and reasons for each file, in the manual-change log at the end of
`.kiro/specs/onehealth-decision-support/tasks.md`. The team reviewed the code, ran it on two
machines, and is responsible for it.
