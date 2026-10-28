# Sentinel-52

**NAFSI Hub Student Data Challenge, Fall 2026 — SENS-D track**
*Proactive Decision-Making Tool for Food Supply & Safety*

Rushikesh Lagad (University of Arkansas) · Sambhavi Patel (University of Arkansas) ·
Naisargi Modha (Northeastern University)

---

## The decision this tool supports

The brief asks us to pick one supply-chain actor and help them make a real decision. We picked a
**regional food bank**, because the brief's three secondary objectives — preserving food
availability, supporting food security, minimizing avoidable food loss — are a food bank's mission
rather than side constraints, and they are in daily, direct tension with protecting health. Discard a
pallet of chicken on a weak signal and people with no alternative go without; distribute it on a
missed signal and the people harmed are the least able to absorb harm.

> **Decision statement.** For each incoming or on-hand lot of FSIS-regulated poultry, the food bank
> must decide within its perishability window whether to **distribute now**, **prioritize for
> immediate distribution**, **hold for review**, or **divert**, given the producing establishment's
> near-term risk, the nutritional need of the communities it serves, and the loss created by
> discarding edible food.

The mechanism is concrete: the USDA mark of inspection carries the establishment number, so an
incoming pallet can be traced to the plant that produced it, and that plant has a public sampling
history.

**This is not** a regulatory determination, an outbreak declaration, or a safety verdict on any food,
establishment or shipment. It reorders attention and surfaces evidence for a human decision.

Full reasoning, requirements and design: `.kiro/specs/onehealth-decision-support/`.
The brief as published: `docs/CHALLENGE_BRIEF.md`.

> **Status.** The analysis under `analysis/` is complete and reproducible as described below. The
> decision layer and the application are in development. Section headings here that say so are
> accurate as of the last commit date.

---

## What the analysis found

US poultry plants are rated by FSIS on **how often** Salmonella is found in their products, and not on
**which** Salmonella. This project builds the missing half.

All recomputed from the public FSIS files, with the full argument and caveats in `report/FINDINGS.md`:
routine positivity has been flat since FY2021 while the serotype mix shifted hard toward Infantis
(3.5% → 36.1% of serotyped chicken isolates), and 86.2% of chicken Infantis isolates are resistant to
three or more drug classes against 3.3% for the Kentucky it displaced. FSIS's own FY2022-2026
indicator is above its baseline rather than 10% below it.

---

## Getting the data

Nothing is committed under `data/raw` or `data/processed`. The 31 FSIS source files are 62 MB of
federal open data that belongs to FSIS, not to us; the processed tables are rebuilt from them.

**Download them by hand.** This is the reliable route and it is the one to use.

```bash
cd analysis
python scripts/01_fetch_fsis.py --print-urls
```

That prints all 31 files as `destination path` and `source url`, tab-separated. Save each one at
`data/raw/<destination path>`. The four folders are `raw_poultry`, `narms_cecal`, `establishments`
and `salmonella_categories`. Then verify:

```bash
python scripts/01_fetch_fsis.py --verify-only
```

Every file is compared against the SHA-256 recorded in `data/MANIFEST.json`, which also holds each
file's direct URL, byte count and FSIS `Last-Modified` date. Neither command touches the network, and
both resolve `data/` relative to the repository, so they work from any directory. `--verify-only`
exits non-zero if any file is missing, and refuses to report success at all if it cannot find the
manifest.

FSIS landing pages, if you would rather navigate than use the URL list:

| Files | Page |
|---|---|
| 13 × `raw_poultry_sampling_data_fy*.zip` | [Raw Poultry Sampling](https://www.fsis.usda.gov/news-events/publications/raw-poultry-sampling) |
| 13 × `fsis_narms_cecal_sampling_fy*.zip` | [NARMS Cecal Sampling](https://www.fsis.usda.gov/news-events/publications/national-antimicrobial-resistance-monitoring-system-narms-cecal-sampling) |
| 2 × `Dataset_EstablishmentCategories*.xlsx` | [Poultry Categorization Data](https://catalog.data.gov/dataset/fsis-poultry-categorization-data) · [aggregated](https://catalog.data.gov/dataset/fsis-poultry-categorization-data-aggregated) |
| 3 × establishment directory CSVs | [Meat, Poultry and Egg Product Inspection Directory](https://www.fsis.usda.gov/inspection/establishments/meat-poultry-and-egg-product-inspection-directory) · [on data.gov](https://catalog.data.gov/dataset/fsis-meat-poultry-and-egg-inspection-directory-by-establishment-number) |

**`--download` is a convenience and it may fail.** As of 2026-10-27 the FSIS CDN returns HTTP 403 to
automated requests, even though the files are unchanged and still public at the URLs in the manifest
— verified in a browser the same day. The script reports this and points you back to the manual
route. The SHA-256 check is identical either way, so a manual download is not a weaker provenance
claim than an automated one.

A hash mismatch is usually not a problem: FSIS replaces the current fiscal-year file quarterly and the
establishment directory weekly, so a `DIFFERS` line normally means FSIS posted an update. The script
names which files differ and continues.

---

## Reproducing the analysis

Requires Python 3.12 or newer. **Install the requirements before anything else** — `02_build_tables.py`
reads two `.xlsx` files and fails on a bare interpreter that has pandas but not `openpyxl`.

```bash
git clone <repo-url> && cd sentinel-52
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# get data/raw in place first, as above
cd analysis
python run_all.py
```

`run_all.py` hash-checks `data/raw` and then builds everything. It stops with instructions if
`data/raw` is empty rather than failing halfway through. Total runtime is about three minutes on one
core. Outputs land in `analysis/outputs/`:

| Output | What it is |
|---|---|
| `key_numbers.json` | Every headline figure quoted anywhere in the report, in one file |
| `category_validation.json` | The FSIS category rebuild checked against three official postings |
| `early_warning_summary_h{3,6,12}.json` | Baselines vs models, by forecast horizon |
| `calibration_h{3,6,12}.json`, `t18_*` | Reliability tables, ECE and Brier for both scorers |
| `ablation_h{3,6,12}.json`, `t19_*` | Leave-one-group-out, establishment-clustered bootstrap |
| `hazard_first_look.json` | Serotype, resistance and enumeration layer |
| `burden_weighting.json`, `t16`–`t17` | Serotype prevalence against illness burden |
| `t1`–`t19` CSVs | The tables behind each figure |
| `figures/` | Figures used in the report |

### Pipeline stages

| Script | Does |
|---|---|
| `01_fetch_fsis.py` | List, fetch or verify the 31 FSIS source files against the manifest |
| `02_build_tables.py` | 1.3 GB of FSIS JSON into tidy parquet tables |
| `03_profile.py` | Descriptive tables, routine samples only |
| `fsis_categories.py` | Rebuild FSIS Category 1/2/3/NA from raw samples |
| `04_validate_categories.py` | Compare the rebuild against FSIS's posted ratings |
| `05_early_warning_baseline.py` | Who fails next: baselines vs models, strict time split |
| `05b_watchlist_comparison.py` | Watch lists compared at equal size, plus lead time |
| `05c_calibration.py` | Reliability curves, ECE and Brier — are the scores believable numbers |
| `05d_ablation.py` | Leave-one-group-out: which feature families actually carry the signal |
| `06_hazard_first_look.py` | Serotype, resistance, enumeration, and the 2024 proposed standard |
| `07_figures.py`, `08_key_numbers.py` | Figures, and every headline number in one JSON |

Layers beyond FSIS, each fetched by its own script and cached under `data/`:

| Script | Source | Why |
|---|---|---|
| `09_fetch_nors.py` | CDC NORS (public Socrata endpoint) | Human illness burden by serotype |
| `10_burden_weighting.py`, `10b_*` | — | Weight serotype prevalence by burden, not count |
| `11_fetch_noaa.py` | NOAA NCEI CDO v2, GSOM monthly | Environmental conditions; needs `NOAA_CDO_TOKEN` |
| `12_fetch_fsis_recalls.py` | FSIS Recall & PHA API | Recalls traceable to an establishment mark |
| `13_fetch_vulnerability.py` | CDC/ATSDR SVI 2022, Census ACS | Population vulnerability; ACS needs `CENSUS_API_KEY` |
| `14_build_synthetic_inventory.py` | — | Synthetic food-bank lot inventory; **no real inventory data exists** |

To rerun a single stage, each script takes explicit paths, for example:

```bash
python scripts/06_hazard_first_look.py --data ../data/processed --out outputs
```

---

## Running the application

```bash
cd app && npm install && npm run build      # or: npm run dev
npm test                                    # the guardrails, against the data the app ships
```

Deployed to GitHub Pages on every push to `main` by `.github/workflows/deploy-pages.yml`. One
page, six sections — current risk, alerts, scenarios, actions, equity, evidence — mapped to
requirements R1–R6 in `app/README.md`. The app computes nothing: every number comes from
`app/public/data/*.json`, built by `17_build_app_data.py` from the same outputs the report uses.

---

## Data

`data/PROVENANCE.md` documents every dataset: source, access date, licence, geographic and time
coverage, update frequency, transformations applied and known limitations.
`data/DATA_DICTIONARY.md` documents every column in every built table, marking which descriptions come
from FSIS and which are this project's own derivations.

Every source is public open data. The only non-public layer is the synthetic lot inventory built by
`14_build_synthetic_inventory.py`; every row of it carries `is_synthetic = True`, and no real food
bank inventory was used anywhere in this project.

**FSIS use restriction, which this project observes:** these data "should not be used to identify
foodborne illness outbreaks, associate samples with foodborne illness outbreaks or determine whether
two or more samples are causally related." Accordingly, every join between FSIS sampling and CDC NORS
illness data in this repository is made at serotype × year, never at establishment level.

---

## AI assistance

Developed with **Kiro** (AWS agentic IDE). Kiro specs, steering files and hooks are in `.kiro/` and
are submitted as part of this work.

The analysis pipeline under `analysis/scripts/` was drafted with Claude (Anthropic) from 2026-10-09
onwards, then reviewed and run end to end against the real source files by the team. Each script
carries a header saying what was AI-drafted and what has actually been tested against live data.

The written report is the team's own work. AI was used for code, figures, tables and docstrings.

**Disclosure.** The React UI under `app/src/` and its tests were written by Claude (Anthropic) on
2026-10-28 from the Kiro spec, not through Kiro, because the Kiro track for the app had not started
with four days to the deadline. The specs, steering, hooks and the app data contract
(`17_build_app_data.py`) are Kiro's. Details in `app/README.md`.

---

## Repository setup

`docs/SETUP.md` covers creating the repository and the GitHub Pages workflow. Judges and reviewers do
not need any of it; cloning and following **Getting the data** is enough.

---

## Submission checklist

See `docs/SUBMISSION_CHECKLIST.md`. **No pushes to this repository after 2026-11-02 16:00 US Central.**
A push after the deadline disqualifies the team.
