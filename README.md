# Sentinel-52

**NAFSI Hub Student Data Challenge, Fall 2026 — Sens-D track**
*Proactive Decision-Making Tool for Food Supply & Safety*

Rushikesh Lagad (University of Arkansas) · Sambhavi Patel (University of Arkansas) ·
Naisargi Modha (Northeastern University)

> **Status: in development.** The challenge brief had not been published to the NAFSI Hub at the time
> this repository was created, so the research question below is the team's own framing and may be
> revised once the brief is available. Everything in `analysis/` is complete and reproducible as
> described.

---

## What this is

US poultry plants are rated by FSIS on **how often** Salmonella is found in their products, and not on
**which** Salmonella. This project builds the missing half: a decision-support tool that weighs what a
positive actually is, alongside the rating a plant already carries.

See `report/` for the full argument. The short version, all recomputed from the public FSIS files:
routine positivity has been flat since FY2021 while the serotype mix shifted hard toward Infantis
(3.5% → 36.1% of serotyped chicken isolates), and 86.2% of chicken Infantis isolates are resistant to
three or more drug classes against 3.3% for the Kentucky it displaced. FSIS's own FY2022-2026
indicator is above its baseline rather than 10% below it.

---

## First-time setup

```powershell
cd sentinel-52
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

Moves the GitHub Pages workflow into place, initialises git and makes the first commit. Options for
rebuilding the data and creating the GitHub repository are in `docs/SETUP.md`.

## Reproducing the analysis

Requires Python 3.12 or newer. Nothing is committed under `data/raw` or `data/processed`; both are
rebuilt by the steps below.

```bash
git clone <repo-url> && cd sentinel-52
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cd analysis
python run_all.py --download        # fetch the 31 FSIS source files, then build everything
```

`--download` retrieves the source files directly from fsis.usda.gov and verifies each against the
SHA-256 recorded in `data/MANIFEST.json`. FSIS replaces the current fiscal-year file quarterly and the
establishment directory weekly, so a hash mismatch usually means FSIS has posted an update rather than
that anything is wrong; the script reports which files differ and continues.

Total runtime is about three minutes on one core. Outputs land in `analysis/outputs/`:

| Output | What it is |
|---|---|
| `key_numbers.json` | Every headline figure quoted anywhere in the report, in one file |
| `category_validation.json` | The FSIS category rebuild checked against three official postings |
| `early_warning_summary_h{3,6,12}.json` | Baselines vs models, by forecast horizon |
| `hazard_first_look.json` | Serotype, resistance and enumeration layer |
| `t1`–`t15` CSVs | The tables behind each figure |
| `figures/` | Figures used in the report |

### Pipeline stages

| Script | Does |
|---|---|
| `01_fetch_fsis.py` | Retrieve the 31 FSIS source files and verify SHA-256 against the manifest |
| `02_build_tables.py` | 1.3 GB of FSIS JSON into tidy parquet tables |
| `03_profile.py` | Descriptive tables, routine samples only |
| `fsis_categories.py` | Rebuild FSIS Category 1/2/3/NA from raw samples |
| `04_validate_categories.py` | Compare the rebuild against FSIS's posted ratings |
| `05_early_warning_baseline.py` | Who fails next: baselines vs models, strict time split |
| `05b_watchlist_comparison.py` | Watch lists compared at equal size, plus lead time |
| `06_hazard_first_look.py` | Serotype, resistance, enumeration, and the 2024 proposed standard |
| `07_figures.py`, `08_key_numbers.py` | Figures, and every headline number in one JSON |

To rerun a single stage, each script takes explicit paths, for example:

```bash
python scripts/06_hazard_first_look.py --data ../data/processed --out outputs
```

---

## Running the application

See `app/README.md`. *(Build and deployment instructions to be completed as the app is built.)*

---

## Data

`data/PROVENANCE.md` documents every dataset: source, access date, licence, geographic and time
coverage, update frequency, transformations applied and known limitations.
`data/DATA_DICTIONARY.md` documents every column in every built table, marking which descriptions come
from FSIS and which are this project's own derivations.

All source data is US federal government open data published by USDA FSIS. No copyright is asserted.

**FSIS use restriction, which this project observes:** these data "should not be used to identify
foodborne illness outbreaks, associate samples with foodborne illness outbreaks or determine whether
two or more samples are causally related."

---

## AI assistance

Developed with **Kiro** (AWS agentic IDE). Kiro specs, steering files and hooks are in `.kiro/` and
are submitted as part of this work.

The analysis pipeline under `analysis/scripts/` predates the Kiro work and was drafted with Claude
(Anthropic) on 2026-10-09, then reviewed and run end to end against the real FSIS files by the team.
Each script carries a header saying so.

*(Substantial manual changes to Kiro-generated code to be disclosed here as they occur.)*

The written report is the team's own work.

---

## Submission checklist

See `docs/SUBMISSION_CHECKLIST.md`. **No pushes to this repository after 2026-11-02 16:00 US Central.**
A push after the deadline disqualifies the team.
