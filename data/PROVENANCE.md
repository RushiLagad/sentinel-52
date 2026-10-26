# Data provenance

Every dataset used by this project, with its source, access date, licence, coverage, update
frequency, the transformations applied, and what it cannot be used for.

All files were retrieved on **2026-10-09** from `https://www.fsis.usda.gov` and stored byte-for-byte
unmodified. SHA-256 for each of the 31 source files, together with the `Last-Modified` header FSIS
served at retrieval, is recorded in `MANIFEST.json`. `analysis/scripts/01_fetch_fsis.py` re-verifies
every hash and reports any file FSIS has replaced since.

**Licence, all FSIS datasets.** Works of the United States federal government, published by USDA FSIS
as open data. No copyright is asserted and no licence conditions are attached. Attribute to
USDA Food Safety and Inspection Service.

---

## 1. FSIS establishment-specific raw poultry sampling data

| | |
|---|---|
| Source | https://www.fsis.usda.gov/news-events/publications/raw-poultry-sampling |
| Files | 13 ZIP archives, `raw_poultry_sampling_data_fy2014.zip` through `…_fy2026.zip` |
| Accessed | 2026-10-09 |
| Geographic coverage | All FSIS-regulated poultry slaughter and processing establishments, United States |
| Time coverage | 2013-10-01 to 2026-06-30 (FY2014 to FY2026 Q3) |
| Update frequency | Current fiscal year refreshed quarterly; closed years static but occasionally revised |
| Volume | 325,123 samples, 37,695 Salmonella isolates, 35,662 Campylobacter isolates |

**Structure.** One JSON per fiscal year with a `primary_table_data` array (one record per sample,
30 fields) and a `secondary_table_data` array (one record per isolate, 141 fields), plus FSIS's own
field-level data dictionary, which this repo ships as `data_dictionary_primary.csv` and
`data_dictionary_secondary.csv`.

**Transformations applied** (`analysis/scripts/02_build_tables.py`):
- Missing values arrive as the literal string `"NULL"` and are converted to true nulls. The JSON also
  contains bare `NaN` tokens, which Python's `json` accepts but a strict JSON parser rejects.
- `project_code` is mapped to a `product_class` and a `program` (routine, follow-up, exploratory,
  special, low volume, religious exempt). Only routine samples count toward FSIS categories, so most
  analysis filters to `program == "routine"`.
- Censored laboratory strings such as `"<10"` are split into a numeric value and a censoring operator.
- Secondary records are split into Salmonella and Campylobacter isolate tables on the
  `pathogen_number` prefix.
- Serotype strings are whitespace- and case-normalised into `serotype_clean`; the
  "Possible Vaccine Strain" designation is preserved and flagged separately.
- No rows are dropped, imputed or deduplicated.

**Known limitations:**
- Public posting lags collection by roughly 3 to 6 months. FY2026 ends at 2026-06-30 here.
- Salmonella enumeration (CFU) begins at different dates by product class: chicken carcasses
  2022-08-09, parts 2023-01-30, comminuted chicken 2023-02-27, comminuted turkey 2023-04-05. There are
  **no counts at all for turkey carcasses**, and effectively none for follow-up samples.
- **No enumeration exists for anything collected after 2026-04-28**, leaving 447 routine positives in
  the file with no count. Whether this is reporting lag or a change at FSIS is not established.
- 16 routine samples are screened negative yet carry a `"<10"` count.
- Phenotypic MIC testing drops off sharply after FY2023; FSIS sequence-based resistance calls are
  present only from FY2024.
- A handful of records share a `(form_id, pathogen_number)` key, nearly all in FY2014 exploratory
  projects.

**Use restriction stated by FSIS.** These data "should not be used to identify foodborne illness
outbreaks, associate samples with foodborne illness outbreaks or determine whether two or more samples
are causally related." Nothing in this project links samples to illness. FSIS does state the postings
may help industry "identify repetitive subtypes".

---

## 2. FSIS NARMS cecal sampling data

| | |
|---|---|
| Source | https://www.fsis.usda.gov/news-events/publications/national-antimicrobial-resistance-monitoring-system-narms-cecal-sampling |
| Files | 13 ZIP archives, `fsis_narms_cecal_sampling_fy2014.zip` through `…_fy2026.zip` |
| Accessed | 2026-10-09 |
| Geographic coverage | FSIS-regulated slaughter establishments, United States |
| Time coverage | FY2014 to FY2026 |
| Update frequency | Current fiscal year refreshed quarterly |
| Volume | 72,151 cecal samples across cattle, swine, chicken, turkey, sheep, goat and veal |

**Transformations.** Core identifying and result columns retained; Salmonella, Campylobacter,
E. coli and Enterococcus results converted to 1/0 indicators.

**Known limitations.** Sampling is at slaughter, upstream of the product samples in dataset 1, and is
thin per establishment: for young chickens, 142 to 160 establishments are sampled in a given year at
roughly 4 to 5 samples each. 239 of the 261 establishments with routine chicken carcass sampling have
cecal samples at some point, but not in every year. Pooling by company or region is necessary before
these are usable as an upstream signal.

---

## 3. FSIS Meat, Poultry and Egg Product Inspection Directory

| | |
|---|---|
| Source | https://www.fsis.usda.gov/inspection/establishments/meat-poultry-and-egg-product-inspection-directory |
| Files | `MPI_Directory_by_Establishment_Number.csv`, `MPI_Inactive_Directory_by_Establishment_Number.csv` |
| Accessed | 2026-10-09 |
| Geographic coverage | United States, with latitude, longitude and county FIPS per establishment |
| Time coverage | Current snapshot at access date, plus the inactive directory for closed grants |
| Update frequency | Weekly |

**Transformations.** Active and inactive directories concatenated so establishments that closed during
the study period still resolve. Establishment numbers normalised to an `establishment_id` for joining.

**Known limitation.** This is a **snapshot, not a history**. Size, volume category and NPIS status are
from October 2026 and are applied to earlier years as though they never changed. Any finding that
depends on establishment size in, say, FY2018 inherits that error.

---

## 4. FSIS establishment demographic data

| | |
|---|---|
| Source | Same directory page as dataset 3 |
| File | `Dataset_Establishment_Demographic_Data.csv` (264 columns) |
| Accessed | 2026-10-09 |
| Update frequency | Periodic |

**Transformations.** A subset retained: HACCP size, slaughter and processing volume categories, NPIS
participation, exemptions and current Salmonella categories.

**Known limitation.** Same snapshot problem as dataset 3.

---

## 5. FSIS Salmonella verification testing, monthly establishment categories

| | |
|---|---|
| Source | https://www.fsis.usda.gov/science-data/data-sets-visualizations/microbiology/salmonella-verification-testing-program-monthly |
| Files | `Dataset_EstablishmentCategories_202609_0.xlsx`, `Dataset_EstablishmentCategoriesAggregate_202609_0.xlsx` |
| Accessed | 2026-10-09 |
| Time coverage | 52-week window ending 2026-08-29 |
| Update frequency | Monthly, lagging roughly five weeks |

**Role in this project.** Ground truth. FSIS's published Category 1, 2, 3 and NA ratings are what the
rebuild in `analysis/scripts/fsis_categories.py` is validated against.

---

## 6. FSIS monthly category postings, historical (validation set)

| | |
|---|---|
| Source | Same monthly postings page as dataset 5 |
| Files | `validation/posted_categories_202101.csv`, `…_202310.csv`, `…_202608.csv` |
| Accessed | 2026-10-09 |
| Time coverage | 52-week windows ending 2020-12-26, 2023-09-30 and 2026-06-27 |

**Transformations.** Read from FSIS's posted spreadsheets in a browser and saved as CSV with column
names standardised. Each row retains its `source_url`. Older postings use different header rows and
column names (`EstablishmentNumber`, `SalmCat`), which the ingest handles by detecting the header row.

**Why three windows.** To test the category rebuild across a span in which FSIS changed its counting
rules, in particular the exclusion of possible vaccine strains from 1 April 2024.

---

## Derived data

`data/processed/*.parquet` is produced entirely by `analysis/run_all.py` from the files above. It is
reproducible from `data/raw` and contains no external data. The monthly panel
(`panel_monthly_h*.parquet`) is a derived unit-level table, one row per establishment, product class
and month-end, built in `analysis/scripts/05_early_warning_baseline.py`.

## Caveat carried into every result

The FSIS category rebuild matches FSIS's own published ratings on 2,757 of 2,764 joined rows across
the three validation windows (99.75%), with no false Category 3. Reaching that required one rule that
is **inferred from FSIS's tables and not found in FSIS documentation**: when a 52-week window holds
fewer samples than the performance standard's sample set, the allowed number of positives is the
standard scaled to the samples actually taken and rounded up. It is empirical. Any downstream result
that depends on a rebuilt category inherits that assumption.

---

## 7. CDC National Outbreak Reporting System (NORS)

| Field | Value |
|---|---|
| **Source** | CDC, National Outbreak Reporting System, public open-data release |
| **URL** | https://data.cdc.gov/dataset/NORS/5xkq-dg7x (API: `data.cdc.gov/resource/5xkq-dg7x.json`) |
| **Access date** | 2026-10-26 |
| **Licence** | US federal government public-domain data, published on CDC's open data portal. No registration or agreement required. |
| **Geographic coverage** | United States, by state; multistate outbreaks are reported as "Multistate". Excludes outbreaks with exposure outside the US and cruise ships with international ports of call. |
| **Time coverage** | 1971 to 2023 in the public release. This project uses 2014 to 2023, the window that overlaps FSIS sampling. |
| **Update frequency** | Annual. Final data lag 12 to 18 months after the reporting year, so recent years are under-reported and records can be revised after close-out. |
| **Fetched by** | `analysis/scripts/09_fetch_nors.py` |
| **Cached at** | `data/nors/nors_poultry_serotype_year.csv`, `data/nors/nors_salmonella_attribution.csv` |

### Transformations applied

Server-side aggregation through the Socrata API: Salmonella foodborne outbreaks, 2014 to 2023,
grouped by year, IFSAC food category and serotype. Only aggregate counts are retrieved; no
individual outbreak records are stored in this repository.

Multi-serotype outbreaks appear in NORS as semicolon-joined strings. These are attributed to the
first listed serotype rather than counted once per serotype, which would double-count illnesses.
Composite rows are 9 of the poultry set and 5.4 percent of poultry hospitalizations; both figures
are reported in `burden_weighting.json` rather than left implicit.

### Known limitations

- Outbreak-associated illness is a small and biased subset of all salmonellosis. Most cases are
  sporadic and never enter NORS. Burden figures here are therefore a floor on harm, not an estimate
  of it.
- IFSAC food attribution is absent for a large share of outbreaks. Across Salmonella foodborne
  outbreaks 2014 to 2023, 710 of 1,284 carry no IFSAC category, covering 1,891 of 5,846
  hospitalizations, which is 32.3 percent. Poultry-attributed burden is consequently a floor.
- Counts per serotype are small, and single large outbreaks dominate several of them. Every burden
  figure in this project is reported alongside the share contributed by its largest single outbreak.
- The public release ends at 2023 while FSIS sampling runs to FY2026, so the two series do not cover
  the same final years.

### A note on the dataset circulated by the organisers

On 2026-10-26 the challenge organisers emailed participants a NORS extract and an FSIS
ready-to-eat sampling file, stating that the data was conditionally granted for the challenge and
asking that it not be shared outside the team.

**Neither file is in this repository and neither is read by any script here.** This project uses the
public CDC endpoint instead, for two reasons: the submission requires a public repository that judges
can reproduce from, which a redistribution restriction would prevent; and the public release carries
`ifsac_category`, the standardized food attribution that the emailed flat file lacks and that this
analysis depends on. The emailed extract was used only as a private cross-check and is not required
to reproduce any result.

The FSIS attachment is a 20-row schema sample rather than a dataset, and contains no analysable data.

---

## 8. FSIS Recalls and Public Health Alerts

| Field | Value |
|---|---|
| **Source** | USDA FSIS Recall and Public Health Alert API |
| **URL** | `https://www.fsis.usda.gov/fsis/api/recall/v/1` |
| **Access date** | 2026-10-26 |
| **Licence** | US federal government public domain. No key, no registration. |
| **Geographic coverage** | United States, distribution states listed per recall |
| **Time coverage** | Full archive; this project uses 2014 onward to match the sampling panel |
| **Update frequency** | Continuous, as recalls and alerts are issued |
| **Fetched by** | `analysis/scripts/12_fetch_fsis_recalls.py` |
| **Cached at** | `data/fsis_recalls/` |

### Decision value

A recall is a fact about product already in commerce, not a prediction. In the decision layer a recall
touching held stock outranks any model score, which is why it sits at the top of the alert queue
rather than being folded into a risk number.

### Transformations applied

Full archive retrieved as one JSON array (about 2,000 records). HTML entities decoded, whitespace
normalised, duplicates dropped on recall number, date and title. Two flags derived: poultry mentioned
in the title, and Salmonella mentioned in reason, title or summary. Establishment marks extracted from
product text as described below.

### Known limitations

- **`field_establishment` holds company names, not establishment numbers**, so it does not join to the
  sampling panel. Establishment numbers appear only inside the product text, as USDA marks of
  inspection ("EST. P-50784", "EST. 18004", "Est. 45640", "EST. P 20935A"). The fetch script extracts
  and normalises them.
- **Recovery is partial.** Of 563 poultry-or-Salmonella recalls from 2014 on, **206, or 36.6 percent,
  carry a recoverable mark** (measured by `12_fetch_fsis_recalls.py` on 2026-10-26). The remainder cannot be tied to a plant from this feed at all. Any
  statement about recall history per establishment is therefore a lower bound, and the application
  must not present an establishment with no linked recall as one that has never been recalled.
- A single recall can carry several marks, because one notice may cover product from several plants.
- Ten of the 563 relevant recalls carry FSIS's own `related_to_outbreak` flag set to true.
- `field_related_to_outbreak` is FSIS's own published flag on a recall notice. It is public record and
  distinct from the sampling-data restriction, which forbids *us* inferring outbreak links from
  sampling results. We report the flag as published and infer nothing from it.
