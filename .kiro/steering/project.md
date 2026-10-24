---
inclusion: always
---

# Sentinel-52: project guidance

Team Sentinel-52, NAFSI Hub Student Data Challenge Fall 2026, Sens-D track
("Proactive Decision-Making Tool for Food Supply & Safety").
Members: Rushikesh Lagad (University of Arkansas), Sambhavi Patel (University of Arkansas),
Naisargi Modha (Northeastern University). Submission deadline 2026-11-02, 16:00 US Central.

## What this project is about

US poultry plants are graded by FSIS on **how often** Salmonella is found in their products, and not
at all on **which** Salmonella. This project builds the missing half: a decision-support view that
weighs what a positive actually is, next to the rating a plant already gets.

The supporting evidence, all recomputed from the public FSIS files in this repo:

- Routine positivity has been roughly flat since FY2021. Chicken parts 7.6% (FY2021) to 8.1% (FY2026).
- The serotype mix changed underneath it. Infantis went from 3.5% of serotyped chicken isolates
  (FY2015) to 36.1% (FY2026); Kentucky fell from 40.1% to 16.6%.
- That matters because 86.2% of chicken Infantis isolates are resistant to three or more drug classes
  in FSIS's own sequence-based calls, against 3.3% for Kentucky and 0.4% for Enteritidis.
- FSIS's own FY2022-2026 indicator (share of samples positive for Infantis, Enteritidis or
  Typhimurium) is **above** its 4.22% baseline, not 10% below it as targeted.
- Failure concentrates in small plants: Category 3 covers 25.4% of rated very small plants against
  6.7% of large ones.
- Predicting *who* fails is close to solved by arithmetic. A transparent binomial projection reaches
  AUROC 0.917 over a 6-month horizon; gradient boosting adds about 0.009. A model is not the story.

## Hard constraints, do not violate

1. **FSIS use restriction.** These data "should not be used to identify foodborne illness outbreaks,
   associate samples with foodborne illness outbreaks or determine whether two or more samples are
   causally related." Never build a feature that links samples to illness, to each other as a
   transmission chain, or to an outbreak. Process control at a single plant is the frame.
2. **No pushes to the repository after the submission deadline.** Any push after 2026-11-02 16:00 CT
   disqualifies the team.
3. **Reproducibility is graded.** Judges must reproduce every reported result from the README alone.
   Anything that cannot be rerun from `data/raw` plus the scripts does not belong in the report.
4. **Only publicly available external data**, used in compliance with its licence, and every dataset
   must be added to `data/PROVENANCE.md` with source, access date, licence, coverage, update
   frequency, transformations and limitations.
5. **The written report is the team's own work.** Do not draft report prose. Generating code,
   docstrings, tests and figures is in scope; writing the narrative is not.

## How to be useful here

- **Do not inflate results.** This team would rather report a small effect honestly than a large one
  loosely. Always give the uncertainty next to the point estimate, and say plainly when a difference
  is within noise. If a model barely beats a baseline, say so and keep the baseline.
- **Prefer the transparent method.** A plant manager or an FSIS district has to act on this. Arithmetic
  anyone can audit beats a model nobody can question, unless the model is clearly better and the
  margin survives resampling by establishment.
- **Establishment-clustered uncertainty.** Month-end rows for one plant are not independent. Any
  interval or significance claim must resample whole establishments, never rows.
- **Watch for composition effects.** FSIS changes which plants it samples. Before reporting any trend,
  check it against a fixed panel of plants sampled throughout. The apparent rise in comminuted chicken
  positivity is mostly a change in who gets sampled.
- **Never invent a number.** Every figure quoted anywhere traces to `analysis/outputs/key_numbers.json`
  or a named CSV in `analysis/outputs/`. If a number is not there, compute it and put it there.

## Repository layout

- `analysis/` — the Python pipeline. `run_all.py` runs scripts 01 to 08 in order and rebuilds
  everything from `data/raw` in about three minutes.
- `analysis/scripts/fsis_categories.py` — rebuilds FSIS Category 1/2/3/NA from raw samples. Validated
  at 99.75% against three official postings. Treat this module as load-bearing; change it only with a
  re-run of `04_validate_categories.py`.
- `data/` — `MANIFEST.json` (SHA-256 of all 31 source files), `PROVENANCE.md`, `DATA_DICTIONARY.md`,
  `raw/` (not committed), `processed/` (not committed, rebuildable), `validation/` (three FSIS postings).
- `app/` — the decision-support web application. React, deployed to GitHub Pages.
- `report/` — figures and the report source. The PDF is a required deliverable.
- `.kiro/` — specs, steering and hooks. These are themselves graded submission artifacts, so keep them
  current rather than tidying them up at the end.

## Conventions

- Python 3.12+, pandas, numpy, scikit-learn, scipy, matplotlib, pyarrow. No new heavy dependency
  without a reason, and anything added goes in `requirements.txt` the same commit.
- Scripts take `--data` and `--out` paths, never hardcode absolute paths, and write results as CSV or
  JSON into `analysis/outputs/`.
- Figures: colour-blind-safe palette already in use, blue `#2a78d6`, orange `#eb6834`, aqua `#1baf7a`
  on surface `#fcfcfb`. One measure per axis, never a dual axis, legend whenever two or more series.
- Any file containing code you generated carries a header noting it was AI-assisted, consistent with
  the existing scripts, and substantial manual edits to generated code get disclosed in the README.
