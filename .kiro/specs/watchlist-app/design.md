# Design: Sentinel-52 watch-list application

## Architecture

A single-page React application, built with Vite, deployed as static files to GitHub Pages.
There is no backend and no runtime network call. Everything the application shows is computed
ahead of time by the analysis pipeline and shipped as JSON alongside the bundle.

```
analysis/scripts/*.py          existing, validated pipeline
        │
        ├── analysis/outputs/*.json|csv        evidence files, already produced
        │
        └── analysis/scripts/09_build_app_data.py        NEW
                    │
                    └── app/public/data/*.json           app-shaped, small, versioned
                                │
                            app/src/**                   React
                                │
                            app/dist/                    static build -> Pages
```

### Why a separate app-data build step

The analysis outputs are shaped for analysis: wide CSVs, nested JSON, a 15,443-row evaluation frame.
Shipping those to a browser would be slow and would push joining logic into React, where it would be
untested. `09_build_app_data.py` does the joining and shaping once, in Python, next to the code that
already knows the schema, and emits small files with a fixed contract.

It also means the application cannot silently disagree with the report: both read from the same
upstream outputs, and the shaping step is in the repository and reproducible.

### Why no backend

Submission item 3 says judges must be able to run it from build and deployment instructions. A static
bundle is the only deployment that cannot be broken by a dead server, an expired key or a cold start
on the evening of judging.

---

## Data contract

`09_build_app_data.py` writes these files into `app/public/data/`. Every file carries a `meta` object
with `generated_at`, `source_files`, and `pipeline_commit` so Requirement 6.2 is satisfiable.

| File | Contents | Feeds |
|---|---|---|
| `watchlist.json` | one row per currently rated establishment and product-class unit, with identifiers, current category, trailing window counts, allowed positives, risk score, rank, and consecutive months on list | R1, R2 |
| `scenario.json` | the measured operating points and the precision/recall curve over list size | R2 |
| `leadtime.json` | share-on-list-k-months-before, per strategy, with denominators | R3 |
| `establishments/<id>.json` or one `history.json` keyed by unit | per-unit sampling history by window | R4 |
| `context.json` | FSIS indicator series, Category 3 by size, serotype shares and resistance | R5 |
| `caveats.json` | method caveats, validation result, FSIS use restriction | R6 |

### Risk score

The default scorer is the **binomial projection**, not the gradient-boosting model, even though
gradient boosting scores slightly higher: AUROC 0.926 with a bootstrap interval of 0.913 to 0.938,
against 0.917 and 0.903 to 0.931 for the projection. The intervals overlap heavily. The projection is
arithmetic a reviewer can reproduce by hand from the same two numbers FSIS already publishes, and for
a tool whose output is "go inspect this plant," being checkable matters more than a third decimal
place of AUROC.

The application SHALL let the user switch to the gradient-boosting score, and SHALL show both
intervals when it does, so the choice is visible rather than buried.

---

## Screens

### 1. Watch list (default route)

A filter row above a sortable table. The budget control from Requirement 2 lives here, directly above
the list, because changing it changes the list. Filters: state, size class, product class, current
category, text search.

Each row shows the evidence, not just a verdict: samples and positives in the trailing window, the
allowed count, and how far over or under the unit sits. A user should be able to tell why a unit
ranks where it does without opening anything.

Already-Category-3 units are shown in a visually distinct, labelled group. They are not predictions.

### 2. Scenario

The three measured operating points as a small-multiple comparison, plus a precision/recall curve
across list size with the current budget marked. Units per month shown alongside percentages
throughout, because "65 units a month" is a staffing decision and "10 percent" is not.

### 3. Lead time

A grouped bar chart, k = 1 through 6 months, one group per strategy. Denominators stated on the
screen, including the 28 entries that arrived from an unrated state.

### 4. Establishment detail

Reached from a watch-list row. Sampling history, position against the standard, serotype panel with
an explicit empty state.

### 5. Context

The five surveillance facts from Requirement 5, each with its source file named.

### 6. Methods and caveats

Validation result, the inferred rounding rule, the FSIS use restriction, links to `PROVENANCE.md`
and `DATA_DICTIONARY.md`.

---

## Components

```
App
├── DataProvider            fetch + cache the JSON, expose load errors
├── Layout                  nav, theme toggle, footer with provenance links
├── WatchlistPage
│   ├── BudgetControl       drives list size; shared state with ScenarioPage
│   ├── FilterBar
│   ├── WatchlistTable      sortable, virtualised above ~200 rows
│   └── UnitRow
├── ScenarioPage
│   ├── OperatingPointCards
│   └── PrecisionRecallChart
├── LeadTimePage
├── EstablishmentPage
├── ContextPage
├── MethodsPage
└── shared/
    ├── Chart               wrapper enforcing single y-axis, legend, table view
    ├── TableView           the required tabular fallback for every chart
    ├── SourceNote          filename + generated_at, per panel
    └── EmptyState          for missing serotype data and failed loads
```

### State

Budget share and scorer choice are application-level state, because the watch list and the scenario
screen must agree. Filters are page-local. No state library; React context is sufficient at this size.

### Routing

Hash-based routing. A Pages deployment at `/<repo>/` breaks browser-history routing on refresh
unless the server rewrites, and Pages does not rewrite. `vite.config.js` sets `base: '/sentinel-52/'`.

---

## Visual design

Charts follow the project's dataviz rules: categorical hues assigned in fixed order and never cycled,
one y-axis per chart, thin marks, a legend whenever two or more series are present, direct labels
where they fit, recessive grid and axes, and text in ink tokens rather than series colour.

Palette: blue `#2a78d6`, orange `#eb6834`, aqua `#1baf7a` on surface `#fcfcfb`, with dark-mode steps
selected against the dark surface rather than flipped. The palette must be run through the validator
before it ships; adjacent-pair CVD separation is not something to eyeball.

Category and risk are never colour alone. Category 3 carries a label and a shape, not just a red fill.

---

## Error handling

| Failure | Behaviour |
|---|---|
| A data file 404s | Named error panel saying which file, with the expected path. Other panels continue to render. |
| A data file parses but is missing a key | Panel renders an empty state naming the key, rather than crashing the page. |
| A unit has no serotype data | Explicit "no serotype recorded for these positives", plus the national share for context. |
| Zero rows after filtering | "No units match these filters", with a reset control. |

A blank screen is the one unacceptable failure mode, because a judge will read it as broken rather
than as empty.

---

## Testing

- **Unit:** risk ranking order, budget-to-count arithmetic, filter composition, and the formatters
  that turn a share into units per month.
- **Contract:** a test asserting each `app/public/data/*.json` has the keys the components read.
  This is the test that catches a pipeline change silently breaking the app, which is the most likely
  real failure given the analysis code is still being touched.
- **Render:** each page renders without crashing against the committed fixture data.
- **Accessibility:** automated check for colour contrast and for the presence of a table view per chart.

Vitest plus React Testing Library. The contract test is the one that earns its keep; the others are
there so a refactor does not quietly break ranking.

---

## Build and deploy

```
cd app
npm install
npm run dev          # local
npm run build        # -> app/dist
```

Deployment uses the workflow already written at `docs/pages-workflow-for-later.yml`. It stays out of
`.github/workflows/` until the app exists, because a Pages workflow with nothing to build fails on
every push. When the app builds locally, move it into place and set Settings > Pages > Source to
GitHub Actions.

---

## Open question

The challenge questions have never been published. Requirement coverage here is derived from the
track title, "Proactive Decision-Making Tool for Food Supply & Safety", and from the six required
submission items. If the questions are released before the deadline, revisit Requirements 1 and 5
first; the scenario and lead-time screens are likely to survive any phrasing, since they are what
makes the tool a decision tool rather than a dashboard.

---

## Addendum: the human-outcome layer

Added 2026-10-26, after the organisers circulated NORS as a recommended dataset.

### What changed

The application was originally going to rank establishments on projected failure alone. It now also
carries an outcome layer: which serotypes actually cause outbreak-associated illness, from CDC's
National Outbreak Reporting System.

This is the difference between a dashboard and a decision tool. Projection answers "who is about to
breach a standard." Burden answers "and does that matter to anyone's health." A unit drifting toward
Category 3 on Kentucky is a compliance problem. A unit drifting on Enteritidis is a public health
problem. The tool should not pretend those are the same.

### Data source and why not the emailed file

NORS is pulled from CDC's public Socrata endpoint, `data.cdc.gov/resource/5xkq-dg7x`, by
`analysis/scripts/09_fetch_nors.py`. The organisers also circulated a NORS extract by email under a
no-redistribution condition. **That file is not in this repository and is not used by any script.**
Using the public endpoint keeps the pipeline reproducible by anyone and keeps restricted material out
of a public repo.

The public file is also the better input: it carries `ifsac_category`, the standardized food
attribution, which the emailed flat file does not. Without it, attributing an outbreak to poultry
means parsing free text, which is neither reproducible nor defensible.

Its one disadvantage is coverage: public NORS currently ends at 2023 while FSIS sampling runs to
FY2026. The report must state that the two series do not end in the same year.

### New data files

| File | Contents | Feeds |
|---|---|---|
| `burden_weighting.json` | serotype burden, policy comparison, attribution completeness, caveats | R9 |
| `t16_nors_poultry_burden_by_serotype.csv` | per-serotype outbreaks, illnesses, hospitalizations, deaths, single-outbreak dominance | R9 |
| `t17_chicken_prevalence_vs_burden.csv` | FSIS isolate share against NORS burden, per serotype | R9 |

### Burden weight

The weight is hospitalizations per serotype over 2014 to 2023, poultry-attributed. It is applied as a
reordering of the existing risk score, never as a replacement, and the unweighted order stays one
click away. Two reasons to keep both visible: the counts are small enough that one outbreak can move
a serotype several places, and a regulator may have a statutory reason to care about a breach
regardless of its health consequence.

Serotypes whose burden comes more than 80 percent from a single outbreak are labelled as such on
every screen that uses them. Reading is at 98.5 percent, Typhimurium at 100 percent, Infantis at 80.6
percent. Enteritidis, at 27.0 percent across 62 outbreaks, is the only poultry serotype whose burden
figure rests on a broad base, and that needs saying up front rather than burying.

### The constraint that shapes every join

The FSIS data licence forbids linking establishments to illness outbreaks. Every join in this layer is
at serotype and year. No establishment identifier is ever carried into NORS-derived code, and no
screen places a plant name next to an outbreak. This is a design constraint, not a preference, and
the contract test should assert that the burden data files contain no establishment column.
