#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-27.
# -----------------------------------------------------------------------------
"""Regenerate data/DATA_DICTIONARY.md from the built tables. Task 1.6, deliverable 4.

The dictionary covers every table this project builds, not only the FSIS ones:
the processed parquet tables, the four layers fetched from outside FSIS, the
simulated inventory, and the decision layer's own output tables.

Two rules make it trustworthy rather than decorative.

  1. Provenance per field. Descriptions taken verbatim from the dictionary FSIS
     ships inside the raw files are marked *(FSIS)*. Everything this project
     derives is marked *(derived)* and described here. A reader can always tell
     whose claim a description is.

  2. It refuses to invent. A column with no description in this file is written
     out as UNDOCUMENTED rather than given a plausible-sounding gloss, and
     --check exits non-zero while any remain. A dictionary that quietly makes
     things up is worse than no dictionary, because it reads as authoritative.

    python scripts/19_build_data_dictionary.py --repo .. --out ../data/DATA_DICTIONARY.md
    python scripts/19_build_data_dictionary.py --repo .. --check
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

MAXLEN = 300          # FSIS descriptions run long; truncate with a pointer to the CSV

# --------------------------------------------------------------------------- #
# descriptions for everything this project derives
# --------------------------------------------------------------------------- #
DERIVED: dict[str, str] = {
    # ---- processed tables, built by 02_build_tables.py / fsis_categories.py
    "establishment_id": "Establishment number normalised to an integer for joining to the MPI directory. FSIS recommends joining on this rather than on establishment_number, which can be reused over time.",
    "product_class": "Product category implied by project_code: chicken_carcass, chicken_parts, comminuted_chicken, turkey_carcass, comminuted_turkey, or an exploratory class.",
    "program": "Sampling programme implied by project_code: routine (HC_*), followup (F_*), exploratory, special, low_volume or religious_exempt.",
    "species": "chicken or turkey, from product_class.",
    "fy": "Federal fiscal year of collection_date (1 October to 30 September).",
    "fy_file": "Fiscal-year file the record was read from.",
    "sal_result": "1 if salmonella_sp_analysis is Positive, 0 if Negative, null otherwise.",
    "sal_result_cat": "As sal_result, but positives typed as a possible vaccine strain are set to 0. This is how FSIS counts for categorisation from 1 April 2024.",
    "sal_vaccine_only": "True when the only Salmonella isolate for the sample is typed 'Possible Vaccine Strain'.",
    "campy_result": "1/0 from the 1 mL or 30 mL Campylobacter analysis, whichever was run.",
    "campy_method": "Which Campylobacter analysis produced campy_result (1ml or 30ml).",
    "sal_cfu": "Numeric part of the Salmonella enumeration result. Every reported value is either '<10' or a number of 10 or more.",
    "sal_cfu_sign": "Censoring operator parsed from the enumeration string: '<' or '='.",
    "sal_cfu_unit": "ml (carcass and parts rinsate) or g (comminuted product).",
    "sal_cfu_ge10": "True when the sample was enumerated at 10 CFU or more, that is quantifiable rather than '<10'. Null when no count was reported.",
    "serotype_clean": "Serotype string normalised for grouping: whitespace and case regularised, FSIS's vaccine-strain annotation preserved as a distinct value rather than folded into Typhimurium.",
    "category": "FSIS Salmonella Category 1, 2, 3 or NA, rebuilt from raw samples on the 52-week moving window by fsis_categories.py. Validated against three official postings at 99.75% agreement over 2,764 rows.",
    "category_posted": "The category FSIS actually published for this window, read from the posted category files in data/validation.",
    "category_rebuilt": "The category this project's rebuild produced for the same window. Compared against category_posted by 04_validate_categories.py.",
    "window_end": "Saturday ending the 52-week moving window the row describes.",
    "n52": "Routine samples in the 52-week window.",
    "pos52": "Routine positives in the 52-week window, counted the way FSIS counts for categorisation.",
    "spare3": "Positives the unit could still record in this window before crossing into Category 3. Lower means closer to failing.",
    "projection": "Binomial projection of the probability the unit enters Category 3 within the forecast horizon. The transparent baseline scorer, and the default in the decision layer at short horizons because it is the better calibrated there.",
    "gb": "Gradient-boosting score for the same event. Better ranked at most horizons, better calibrated only at 6 months.",
    "y": "Outcome. 1 if the unit entered Category 3 within the forecast horizon, 0 otherwise. The label every error rate in this project is measured against.",

    # ---- CDC NORS, fetched by 09_fetch_nors.py
    "cat": "IFSAC food category the outbreak was attributed to, from NORS field ifsac_category. The join to FSIS is made on this and on year, never on an establishment.",
    "sero": "Serotype or genotype as NORS records it (field serotype_or_genotype). Not harmonised with FSIS serotype spelling; matched case-insensitively on the leading token.",
    "nb": "Number of outbreaks in the group.",
    "ill": "Sum of reported illnesses across those outbreaks.",
    "hosp": "Sum of reported hospitalisations. Sparse: a single large outbreak can dominate a serotype-year, and 10b flags any share above 80% as resting on one event.",
    "dth": "Sum of reported deaths.",

    # ---- NOAA GSOM, fetched by 11_fetch_noaa.py
    "state": "Two-letter US state code.",
    "date": "Month the observation covers, as the first day of that month.",
    "PRCP": "Mean monthly precipitation across the state's station panel, in millimetres. NOAA CDO was queried with units=metric.",
    "TAVG": "Mean monthly average temperature across the station panel, in degrees Celsius.",
    "TMAX": "Mean monthly maximum temperature across the station panel, in degrees Celsius.",
    "n_stations": "Stations contributing to that state-month. Fewer stations means a noisier mean, so this is kept rather than hidden.",
    "year": "Calendar year.",
    "month": "Calendar month, 1 to 12.",
    "station": "NOAA station identifier.",
    "name": "NOAA station name.",
    "datacoverage": "NOAA's own completeness fraction for the station over the requested window. Stations are chosen deterministically by this descending, then by id, so the panel is reproducible.",
    "mindate": "First date NOAA holds for the station.",
    "maxdate": "Last date NOAA holds for the station.",
    "latitude": "Station latitude.",
    "longitude": "Station longitude.",

    # ---- FSIS recalls, fetched by 12_fetch_fsis_recalls.py
    "recall_number": "FSIS recall case number.",
    "recall_date": "Date FSIS published the recall or public health alert.",
    "risk_level": "FSIS risk level for the recall.",
    "recall_class": "FSIS recall classification (I, II, III).",
    "recall_type": "Whether the notice is a recall or a public health alert.",
    "reason": "FSIS's stated reason for the recall.",
    "outbreak_related": "FSIS's own flag that the recall is outbreak-associated. Carried through as published; this project draws no causal link of its own between any establishment and any illness.",
    "active_notice": "Whether FSIS still lists the notice as active.",
    "company": "Recalling company as FSIS names it.",
    "est_marks": "Establishment marks recovered from the notice text by regular expression. Recoverable for only 206 of 563 poultry-or-Salmonella notices (36.6%), so an establishment with no linked recall may simply be unresolvable rather than clean.",
    "n_states": "Number of states in the distribution list.",
    "states": "Distribution states as listed.",
    "is_poultry_title": "True when the notice title matches this project's poultry filter.",
    "is_salmonella": "True when the notice mentions Salmonella.",
    "title": "Notice title as published.",
    "url": "Link to the notice on fsis.usda.gov.",

    # ---- CDC/ATSDR SVI, fetched by 13_fetch_vulnerability.py
    "fips": "Five-digit county FIPS code, zero-padded.",
    "state_name": "State name as SVI spells it.",
    "county": "County name as SVI spells it.",
    "population": "County population as carried in the SVI release.",
    "svi_overall": "CDC/ATSDR Social Vulnerability Index 2022 overall percentile rank (RPL_THEMES), 0 to 1. A percentile within the United States, so it is relative deprivation, not absolute. Static across the sampling window.",
    "svi_socioeconomic": "SVI theme 1 percentile rank: socioeconomic status.",
    "svi_household": "SVI theme 2 percentile rank: household characteristics.",
    "svi_minority_status": "SVI theme 3 percentile rank, as CDC/ATSDR names and constructs it. Carried through unchanged; this project does not use it as a standalone criterion for any decision.",
    "svi_housing_transport": "SVI theme 4 percentile rank: housing type and transportation.",
    "acs_name": "Census ACS place name, present only when the ACS fetch succeeded.",
    "acs_population": "Census ACS 5-year population estimate, present only when the ACS fetch succeeded. Margins of error are not carried through, so county differences of a point or two are noise.",

    # ---- simulated inventory, built by 14_build_synthetic_inventory.py
    "lot_id": "Identifier for a SIMULATED lot. The prefix records the generator seed.",
    "is_synthetic": "Always True. Present on every row so that no consumer of this table can mistake it for real food-bank inventory.",
    "establishment_number": "Establishment mark of the real FSIS plant the simulated lot is attributed to.",
    "establishment_name": "Name of that real plant.",
    "source_state": "State of that plant.",
    "source_county": "County of that plant.",
    "haccp_size": "FSIS HACCP size category of that plant (Large, Small, Very Small).",
    "received_date": "SIMULATED date the lot arrived at the food bank.",
    "use_by_date": "SIMULATED use-by date.",
    "shelf_life_days": "SIMULATED shelf life in days, drawn per product class. Short for fresh carcass and parts, long for frozen comminuted and turkey.",
    "pounds": "SIMULATED weight of the lot. Not a measurement of anything.",
    "dest_county": "SIMULATED destination county, drawn weighted by vulnerability within the service state.",
    "dest_fips": "FIPS code of that destination county.",
    "dest_svi_overall": "svi_overall of the destination county. Real SVI, attached to a simulated destination.",

    # ---- decision layer, built by 16_decision_layer.py
    "scenario": "Named policy: rule_based_category, conservative, capacity_matched or food_security_weighted.",
    "label": "Human-readable description of the scenario.",
    "lots": "Lots the scenario was evaluated on.",
    "lots_unscored": "Lots with no score within the staleness limit. These are distributed with the gap named, never assumed low risk.",
    "hold_at": "Probability threshold at or above which a lot is held. Horizon-specific: a threshold on an absolute probability does not transfer between forecast horizons.",
    "divert_at": "Probability threshold at or above which a lot is diverted to the cooked-meal channel.",
    "review_capacity_per_week": "Modelled number of lots the food bank can review per week. Null means unlimited.",
    "cook_capacity_lbs_per_week": "Modelled SIMULATED pounds the cooked-meal channel can absorb per week. Diverted pounds beyond it are discarded.",
    "food_security_weight": "0 to 1. Raises the hold and divert thresholds for destinations in the most vulnerable SVI quartile, protecting supply there at the cost of accepting more risk there.",
    "precision": "Of the lots held or diverted, the share from plants that did go on to elevated risk.",
    "recall": "Of the lots from plants that went on to elevated risk, the share held or diverted.",
    "tp": "Held or diverted, and the plant did go on to elevated risk.",
    "fp": "Held or diverted, and the plant did not.",
    "fn": "Distributed, and the plant did go on to elevated risk.",
    "tn": "Distributed, and the plant did not.",
    "pounds_distributed": "SIMULATED pounds distributed, including lots moved early.",
    "pounds_held": "SIMULATED pounds held for review.",
    "pounds_diverted": "SIMULATED pounds sent to the cooked-meal channel.",
    "pounds_discarded": "SIMULATED pounds lost, from a hold that exhausted the shelf life or from diversion beyond the cooked channel's capacity.",
    "avoidable_loss_lbs": "SIMULATED pounds discarded from plants that did NOT go on to elevated risk: the cost of a false alarm.",
    "avoidable_loss_meals": "avoidable_loss_lbs at 1.2 lb per meal, Feeding America's convention.",
    "exposure_lbs": "SIMULATED pounds distributed uncooked from plants whose sampling later deteriorated. NOT a count of illnesses and not an estimate of one; FSIS data cannot attribute illness to an establishment.",
    "exposure_meals": "exposure_lbs at 1.2 lb per meal.",
    "holds_per_week_required": "Reviews per week the scenario demands. Compared against review capacity to show whether a policy is executable at all.",
    "review_capacity_exceeded_by": "holds_per_week_required divided by review capacity. Above 1 means the policy cannot be run as written.",
    "pounds_are_synthetic": "Always True. Marks the row as resting on simulated inventory.",
    "n_distribute_now": "Lots recommended for normal distribution.",
    "n_prioritize": "Lots recommended for immediate distribution, because little shelf life remains.",
    "n_hold_for_review": "Lots recommended for review. High-consequence.",
    "n_divert": "Lots recommended for the cooked-meal channel. High-consequence.",
    "svi_quartile": "Quartile of destination county svi_overall, fixed once so every scenario is measured against the same bins.",
    "pounds_offered": "SIMULATED pounds destined for that quartile before any policy is applied.",
    "pounds_withheld": "SIMULATED pounds held or diverted away from that quartile.",
    "withheld_pct": "pounds_withheld as a share of pounds_offered, per quartile. The disparity check compares the most and least vulnerable quartiles and reports the result whichever way it comes out.",
    "share_of_all_distribution_pct": "That quartile's share of all distributed pounds.",
    "days_left": "Shelf-life days remaining when the lot arrived.",
    "scored": "Whether a score within the staleness limit was available for the lot's plant and product class.",
    "score_age_days": "Days between the score's window_end and the lot's arrival. Lots join to scores with a backward as-of join, so a lot only knows what was published before it arrived.",
    "action": "distribute_now, prioritize, hold_for_review or divert.",
    "driver": "One sentence naming the signal that produced the action.",
    "high_consequence": "True for hold and divert. These require explicit human confirmation and carry reversal evidence.",
    "requires_human_confirmation": "True wherever high_consequence is true. Nothing is executed automatically.",
    "alternative_action": "The opposite action, offered with its own cost so the user sees a choice rather than a verdict.",
    "reversal_evidence": "What would change this recommendation, named per lot.",
    "discarded": "True when the lot was lost under this policy.",
    "discard_reason": "Which of the two loss mechanisms applied: a review hold that exhausted the shelf life, or the cooked-meal channel being at capacity.",
}

# Columns that come from an FSIS source file but whose text is NOT in the
# dictionary FSIS ships (the MPI directory, the demographic file, the
# establishment-categories workbooks and the NARMS cecal files carry no
# dictionary of their own). The column is FSIS's; the wording here is ours, and
# it is marked as such rather than passed off as FSIS text.
FSIS_DESCRIBED_HERE: dict[str, str] = {
    # ---- samples.parquet
    "apc_ml_sign": "Censoring operator parsed from the aerobic plate count string ('<' or '=').",
    "eb_ml_sign": "Censoring operator parsed from the Enterobacteriaceae count string.",

    # ---- isolate tables
    "sequenced": "True when the isolate has an SRA accession, that is it was whole-genome sequenced.",
    "vaccine_strain": "True when FSIS typed the isolate as a possible vaccine strain. From 1 April 2024 FSIS excludes these when categorising establishments, and so does this project.",

    # ---- cecal.parquet (NARMS cecal sampling at slaughter)
    "slaughter_class": "Animal class sampled, as FSIS writes it, for example 'Animal-Cattle-Heifer' or 'Animal-Swine-Market Swine'. The cecal programme covers cattle and swine as well as poultry; poultry analysis filters on this.",
    "salmonella_sp": "FSIS's Salmonella result for the cecal sample, as published: Positive or Negative.",
    "salmonella_molecular_serotype": "Serotype FSIS assigned to the cecal Salmonella isolate from sequence data.",
    "salmonella_fsis_number": "FSIS's internal identifier for the cecal Salmonella isolate.",
    "campylobacter": "FSIS's Campylobacter result for the cecal sample: Positive or Negative.",
    "e_coli": "FSIS's generic E. coli result for the cecal sample: Positive or Negative. Generic E. coli is an indicator organism here, not a pathogen finding.",
    "e_coli_sra_accession_number": "SRA accession for the cecal E. coli isolate, where sequenced.",
    "enterococcus": "FSIS's Enterococcus result for the cecal sample: Positive or Negative. Carried as an antimicrobial-resistance indicator organism.",
    "enterococcus_species": "Enterococcus species identified, for example faecalis, faecium, gallinarum.",
    "enterococcus_sra_accession_number": "SRA accession for the cecal Enterococcus isolate, where sequenced.",
    "salmonella_sp_result": "1/0 recoding of salmonella_sp for arithmetic. *(derived)*",
    "campylobacter_result": "1/0 recoding of campylobacter. *(derived)*",
    "e_coli_result": "1/0 recoding of e_coli. *(derived)*",
    "enterococcus_result": "1/0 recoding of enterococcus. *(derived)*",

    # ---- establishments.parquet (MPI directory + demographic file + categories)
    "duns_number": "Dun & Bradstreet number for the company, as listed in the MPI directory.",
    "city": "City of the establishment.",
    "zip": "Postal code of the establishment.",
    "grant_date": "Date FSIS granted inspection. For inactive establishments this is the earliest grant date.",
    "activities": "Semicolon-separated list of inspected activities at the establishment, for example 'Meat Processing; Poultry Slaughter'.",
    "dbas": "Semicolon-separated 'doing business as' names.",
    "district": "FSIS district office code.",
    "circuit": "FSIS inspection circuit code within the district.",
    "size": "FSIS HACCP size category: Large, Small, Very Small, or 'N / A' where not assigned.",
    "fips_code": "Five-digit county FIPS code of the establishment, used to join county vulnerability.",
    "active": "True for establishments from the active MPI directory, False for those from the inactive directory. *(derived)*",
    "inactive_effective_date": "Date the grant of inspection ceased, for inactive establishments.",
    "active_poultry_grant": "True when the establishment holds a current poultry grant of inspection.",
    "inspection_system_npis": "True when the establishment operates under the New Poultry Inspection System.",
    "inspection_system_npis_waiver": "True when the establishment holds a waiver related to NPIS.",
    "poultry_exemption_religious": "True when the establishment operates under the religious-exemption provision for poultry slaughter.",
    "slaughter": "True when the establishment slaughters.",
    "processing": "True when the establishment processes.",
    "processing_volume_category": "FSIS processing volume band, 1 to 5, larger is higher volume. Published as a band rather than a volume.",
    "slaughter_volume_category": "FSIS slaughter volume band, 1 to 5, larger is higher volume.",
    "young_chicken_slaughter": "True when the establishment slaughters young chickens.",
    "young_turkey_slaughter": "True when the establishment slaughters young turkeys.",
    "raw_intact_poultry_processing": "True when the establishment processes raw intact poultry.",
    "raw_non_intact_poultry_processing": "True when the establishment processes raw non-intact poultry, which includes comminuted product.",
    "rte_poultry_processing": "True when the establishment produces ready-to-eat poultry.",
    "nrte_poultry_processing": "True when the establishment produces not-ready-to-eat poultry.",
    "category_start_date": "First day of the 52-week window the posted Salmonella categories cover.",
    "category_end_date": "Last day of that window.",
    "young_chicken_carcasses_category": "Salmonella Category 1, 2 or 3 FSIS posted for young chicken carcasses at this establishment.",
    "young_turkey_carcasses_category": "Posted Salmonella category for young turkey carcasses.",
    "comminuted_chicken_category": "Posted Salmonella category for comminuted chicken.",
    "comminuted_turkey_category": "Posted Salmonella category for comminuted turkey.",
    "chicken_parts_category": "Posted Salmonella category for chicken parts.",
    "company_key": "First two words of the establishment name, upper-cased and stripped of punctuation. A coarse company grouping used only to spot the same firm across several plants; it is not an FSIS identifier and will both split and merge companies. *(derived)*",

    # ---- posted category tables
    "product_class_posted": "Product class exactly as the FSIS posting labels it, before mapping to this project's product_class. *(derived)*",
    "window_text": "The sample-collection period as printed in the posting, kept verbatim so the window can be audited against the source. *(derived)*",
    "source_file": "Which posted-category workbook the row came from. *(derived)*",
    "establishments": "Number of establishments FSIS reports in that category and product class.",
    "percent": "Percentage of rated establishments FSIS reports in that category and product class.",
}


# 02_build_tables.py splits the FSIS secondary table by pathogen and strips the
# organism prefix, so sal_isolates.ampicillin_mic is the dictionary's
# salmonella_ampicillin_mic. Two columns are also renamed outright. Without this
# the generator would report two hundred real FSIS columns as undocumented.
PREFIX = {"sal_isolates.parquet": "salmonella_", "campy_isolates.parquet": "campylobacter_"}
ALIASES = {"apc_ml": "aerobic_plate_count_mpn_ml", "eb_ml": "enterobacteriaceae_mpn_ml"}


# table path -> (title, one-line purpose)
TABLES: list[tuple[str, str, str]] = [
    ("data/processed/samples.parquet", "samples.parquet", "One row per laboratory sample. The analysis backbone."),
    ("data/processed/sal_isolates.parquet", "sal_isolates.parquet", "One row per Salmonella isolate, with serotype, resistance and enumeration detail."),
    ("data/processed/campy_isolates.parquet", "campy_isolates.parquet", "One row per Campylobacter isolate."),
    ("data/processed/cecal.parquet", "cecal.parquet", "NARMS cecal sampling at slaughter."),
    ("data/processed/establishments.parquet", "establishments.parquet", "MPI directory and demographic data, active and inactive."),
    ("data/processed/posted_categories.parquet", "posted_categories.parquet", "Categories FSIS actually published, used to validate the rebuild."),
    ("data/processed/posted_aggregate.parquet", "posted_aggregate.parquet", "FSIS's own aggregate category counts."),
    ("data/nors/nors_poultry_serotype_year.csv", "nors_poultry_serotype_year.csv", "CDC NORS outbreak burden by IFSAC poultry category, serotype and year. Joined to FSIS at serotype and year only."),
    ("data/nors/nors_salmonella_attribution.csv", "nors_salmonella_attribution.csv", "CDC NORS Salmonella burden by food category, all foods."),
    ("data/noaa/noaa_state_month.csv", "noaa_state_month.csv", "NOAA GSOM monthly climate, averaged over a fixed station panel per state."),
    ("data/noaa/noaa_stations_used.csv", "noaa_stations_used.csv", "The station panel itself, so the climate series is reproducible."),
    ("data/fsis_recalls/fsis_recalls_poultry_salmonella.csv", "fsis_recalls_poultry_salmonella.csv", "FSIS recalls and public health alerts filtered to poultry or Salmonella."),
    ("data/vulnerability/vulnerability_county.csv", "vulnerability_county.csv", "CDC/ATSDR SVI 2022 by county, plus Census ACS where the key was accepted."),
    ("data/inventory/lots_synthetic.csv", "lots_synthetic.csv", "**SIMULATED** food-bank lot inventory. Every row carries is_synthetic = True. No real inventory data exists in this project."),
    ("analysis/outputs/t20_scenarios_h3.csv", "t20_scenarios_h3.csv", "One row per policy scenario: error rates, pounds, and both error types in meals."),
    ("analysis/outputs/t21_equity_by_svi_quartile_h3.csv", "t21_equity_by_svi_quartile_h3.csv", "Distribution and withholding by destination SVI quartile, per scenario."),
    ("analysis/outputs/t22_frontier_h3.csv", "t22_frontier_h3.csv", "Threshold sweep: the trade-off between avoidable loss and exposure."),
    ("analysis/outputs/t23_lot_actions_h3.csv", "t23_lot_actions_h3.csv", "Per-lot recommendation for the default scenario, with reversal evidence."),
]


def fsis_descriptions(repo: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for f in ("data_dictionary_primary.csv", "data_dictionary_secondary.csv"):
        for d in (repo / "data" / f, repo / "data" / "processed" / f):
            if d.exists():
                t = pd.read_csv(d)
                cols = [c for c in t.columns if "name" in c.lower()]
                desc = [c for c in t.columns if "desc" in c.lower()]
                if cols and desc:
                    for _, r in t.iterrows():
                        out.setdefault(str(r[cols[0]]).strip(), str(r[desc[0]]).strip())
                break
    return out


def describe(col: str, fsis: dict[str, str], prefix: str = "") -> tuple[str, bool]:
    """Return (markdown description, documented?). Never invents."""
    if col in DERIVED:
        return f"{DERIVED[col]} *(derived)*", True
    # Try the column as written, then its aliased name, then the organism-prefixed
    # name the FSIS dictionary uses, then the derived map under those same keys.
    if col in FSIS_DESCRIBED_HERE:
        t = FSIS_DESCRIBED_HERE[col]
        # A few of these are our own recodings sitting beside FSIS columns; they
        # carry their own marker inline, so do not double-label them.
        tag = "" if t.endswith("*(derived)*") else " *(FSIS column, described by this project)*"
        return f"{t}{tag}", True
    for key in (col, ALIASES.get(col), prefix + col if prefix else None,
                ALIASES.get(col, col) if prefix == "" else prefix + ALIASES.get(col, col)):
        if key and key in DERIVED:
            return f"{DERIVED[key]} *(derived)*", True
        if key and key in fsis and fsis[key] and str(fsis[key]).lower() != "nan":
            col = key
            break
    if col in fsis and fsis[col] and str(fsis[col]).lower() != "nan":
        t = str(fsis[col]).replace("\n", " ").strip()
        if len(t) > MAXLEN:
            t = t[:MAXLEN].rsplit(" ", 1)[0] + " … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)*"
        return f"{t} *(FSIS)*", True
    return "**UNDOCUMENTED — a human must describe this column; this script will not invent one**", False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", type=Path, default=Path(".."))
    ap.add_argument("--out", type=Path, default=None, help="default: <repo>/data/DATA_DICTIONARY.md")
    ap.add_argument("--check", action="store_true", help="write nothing; exit non-zero if any column is undocumented")
    a = ap.parse_args()
    repo = a.repo.resolve()
    out = a.out or repo / "data" / "DATA_DICTIONARY.md"

    fsis = fsis_descriptions(repo)
    parts = [
        "# Data dictionary",
        "",
        "Every column of every table this project builds. Regenerate with "
        "`python scripts/19_build_data_dictionary.py --repo ..` from `analysis/`.",
        "",
        "Descriptions marked *(FSIS)* are taken verbatim from the dictionary FSIS ships inside the raw "
        "sampling files. Those marked *(FSIS column, described by this project)* are FSIS's columns "
        "from source files that carry no dictionary of their own — the MPI directory, the demographic "
        "file, the category workbooks and the NARMS cecal files — so the column is FSIS's and the "
        "wording is ours. Those marked *(derived)* are created by this project. "
        "A column this file cannot describe is written out as UNDOCUMENTED rather than given a "
        "plausible gloss; `--check` fails while any remain.",
        "",
        "Source, licence, coverage and known limitations for every dataset are in `PROVENANCE.md`. "
        "Anything denominated in pounds or meals rests on the **simulated** inventory described below.",
        "",
    ]
    missing, built, skipped = [], 0, []
    for rel, title, purpose in TABLES:
        p = repo / rel
        if not p.exists():
            skipped.append(rel); continue
        df = pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p, low_memory=False)
        parts += [f"## `{title}`", "", purpose, "",
                  f"`{rel}` · Rows: {len(df):,} · Columns: {len(df.columns)}", "",
                  "| Column | Type | Non-null | Description |", "|---|---|---|---|"]
        for c in df.columns:
            text, ok = describe(str(c), fsis, PREFIX.get(title, ""))
            if not ok:
                missing.append(f"{title}.{c}")
            nn = f"{100 * df[c].notna().mean():.0f}%"
            parts.append(f"| `{c}` | {df[c].dtype} | {nn} | {text} |")
        parts.append("")
        built += 1

    if skipped:
        parts += ["## Tables not present in this checkout", "",
                  "These are built by scripts that need network access or a prior stage, and are "
                  "documented above only when present:", ""]
        parts += [f"- `{s}`" for s in skipped] + [""]

    body = "\n".join(parts)
    if a.check:
        print(f"{built} tables, {len(missing)} undocumented columns")
        for m in missing[:20]:
            print("  UNDOCUMENTED", m)
        return 1 if missing else 0

    out.write_text(body, encoding="utf-8")
    print(f"wrote {out}  ({built} tables, {len(df.columns) if built else 0} cols in the last one)")
    if skipped:
        print(f"  {len(skipped)} table(s) not in this checkout: {', '.join(skipped)}")
    if missing:
        print(f"  {len(missing)} UNDOCUMENTED column(s); each is flagged in the file:")
        for m in missing[:20]:
            print("    ", m)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
