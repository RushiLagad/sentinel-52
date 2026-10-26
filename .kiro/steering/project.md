---
inclusion: always
---

# Sentinel-52: project guidance

Team Sentinel-52, NAFSI Hub Student Data Challenge Fall 2026, Sens-D track
("Proactive Decision-Making Tool for Food Supply & Safety").
Members: Rushikesh Lagad (University of Arkansas), Sambhavi Patel (University of Arkansas),
Naisargi Modha (Northeastern University). Submission deadline 2026-11-02, 16:00 US Central.

> **Read "The actual brief" at the end of this file first.** The framing in the next section was
> written before the organizers published the challenge brief on 2026-10-26 and aims at the wrong
> user. The evidence in it is still correct; the intended audience is not.

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

## Data handling, added 2026-10-26

The organisers emailed a NORS extract and an FSIS ready-to-eat sample file under a condition that
they not be shared outside the team. This repository is public.

**Hard rule: neither file, nor anything derived row-by-row from them, goes into this repository.**
NORS is fetched from CDC's public endpoint by `09_fetch_nors.py` instead. The emailed extract is a
private cross-check only. If a result can only be produced from the emailed file, it does not go in
the submission, because a judge could not reproduce it and we would be redistributing restricted data
to do so.

The FSIS licence separately forbids linking establishments to illness outbreaks. Every FSIS-to-NORS
join is at serotype and year. No establishment identifier is ever carried into outcome-layer code,
and no output places a plant name beside an outbreak. Treat this as a correctness property worth a
test, not a style preference.

## What the evidence now says

Prevalence in the supply does not rank with human burden, and this is the project's central finding:

- Kentucky is 16.6 percent of serotyped FSIS chicken isolates and carries zero outbreak-associated
  hospitalizations in NORS across 2014 to 2023.
- Infantis is 36.1 percent, up from 3.5 percent, and carries 31.
- Enteritidis is 22.8 percent and carries 184 across 62 outbreaks.

For chicken, FSIS's own lists are well aimed: the 2024 proposed framework serotypes capture 65.7
percent of chicken-attributed hospitalizations. For turkey they are not: the framework serotypes
capture 6.8 percent, and the highest-burden turkey serotype, Reading, is on neither the framework
list nor the FY2022-26 indicator.

State that asymmetry honestly in both directions. The chicken finding supports FSIS's choices and
should be reported as such; a critique that only reports the turkey half would be selective.

Reading's 135 hospitalizations are 98.5 percent from one 2017 multistate raw-turkey outbreak.
Typhimurium's 22 are from one outbreak, Infantis's 31 are 80.6 percent from one. Enteritidis at 27.0
percent is the only poultry serotype whose burden rests on a broad base. Never quote any of these
figures without the single-outbreak share beside it.

---

# The actual brief, published 2026-10-26

Full extraction in `docs/CHALLENGE_BRIEF.md`; the source is a Google Doc linked by Pedro Ramonetti
Vega. That file is a **summary, not the organizers' verbatim words**, and must be checked against the
original before the report is written.

## The question we are actually answering

> How can a **supply-chain actor** anticipate emerging food-safety risk and make proactive decisions
> that protect health while preserving food availability, supporting food security, and minimizing
> avoidable food loss?

**Not a regulator.** Everything written before 2026-10-26 assumed one. The chosen actor is a
**regional food bank**, because the brief's three secondary objectives are that actor's mission
rather than its side constraints, and because the safety-against-availability conflict the brief asks
us to surface is its daily job. This choice is the team's to revisit.

## Required, and currently missing

Treat these as gaps to close, not options:

- **NOAA/NCEI Climate Data Online.** Required. Needs a free API token in `NOAA_CDO_TOKEN`.
- **FSIS recalls and public health alerts.** Required, and distinct from the sampling data we have.
- **At least two team-added datasets**, one covering food security, vulnerability, supply chain,
  animal health, environmental exposure or infrastructure. Chosen: CDC/ATSDR SVI and USDA food access.
- **Calibration.** We report discrimination only. A score used to hold food must be calibrated.
- **Ablation** giving the marginal value of each added source.
- **Three scenarios minimum**, compared against a rule-based policy.
- **A food-security or equity objective**, with a check on whether holds fall disproportionately on
  high-need communities.
- **Avoidable food loss**, in the same units as missed risk where possible.
- **A One Health system map.**

## Guardrails from the organizers, non-negotiable

1. **Never label a food, establishment or shipment "safe" or "unsafe" on the model alone.** Not in the
   UI, not in a variable name, not in report prose. This is testable and should be tested.
2. The tool is a **prototype**: not a regulatory determination, not an outbreak declaration, not a
   substitute for epidemiologic investigation. Say so in the interface, not only the report.
3. **High-consequence actions require human review** and a statement of the evidence that would
   change them. Nothing auto-executes.
4. Expose uncertainty, provenance and the driving signals on every recommendation.
5. **Test whether recommendations unfairly disadvantage high-need communities**, and report the
   result whichever way it falls.

## Where the marks are

Data science rigor 25 · operational decision support 25 · One Health integration 20 · Kiro 15 ·
team science, reproducibility and communication 15.

Our existing strength is concentrated in the first. The second and third are where the work is.

## The inventory is synthetic, and that must never blur

A food bank's lot-level inventory is not public and we have none. `14_build_synthetic_inventory.py`
generates it from a seeded, documented procedure over real establishments.

Every risk claim rests on real data. Every claim denominated in pounds rests on a simulation. Label
simulated figures as simulated in the UI, the data dictionary, provenance and the report. A judge who
mistakes our inventory for real has been misled by us, and preventing that is a correctness
requirement, not a disclaimer.

## Data handling, unchanged and still binding

The organizers emailed a NORS extract and an FSIS RTE sample file under a no-redistribution
condition. **Neither is in this repository and no script reads them.** NORS comes from the public CDC
endpoint via `09_fetch_nors.py`. If a result can only be produced from the emailed file, it does not
go in the submission.

The FSIS licence separately forbids linking establishments to illness outbreaks. Every FSIS-to-NORS
join stays at serotype and year. No establishment identifier may enter outcome-layer code. Treat this
as a property worth a test, not a preference.
