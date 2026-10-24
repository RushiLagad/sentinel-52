#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-09 and run end to
# end on the real FSIS files. Review it before relying on it.
# -----------------------------------------------------------------------------
"""Build tidy analysis tables from FSIS establishment-specific data products.

Inputs (unmodified FSIS files, see data/raw/MANIFEST.json):
  raw_poultry/raw_poultry_sampling_data_fyYYYY.zip   one JSON per fiscal year
  narms_cecal/fsis_narms_cecal_sampling_fyYYYY.zip   one JSON per fiscal year
  establishments/*.csv                               MPI directory + demographics
  salmonella_categories/*.xlsx                       posted Salmonella categories

Outputs (parquet, in --out):
  samples.parquet          one row per raw poultry sample (FSIS "primary" table)
  sal_isolates.parquet     one row per Salmonella isolate (FSIS "secondary" table)
  campy_isolates.parquet   one row per Campylobacter isolate
  cecal.parquet            one row per NARMS cecal sample (core columns)
  establishments.parquet   one row per establishment_id (active + inactive)
  posted_categories.parquet  FSIS posted category per establishment and product
  posted_aggregate.parquet   FSIS posted counts per category, product and HACCP size
  plus data dictionaries / project codes as CSV and build_report.json

Usage:
  python scripts/02_build_tables.py --raw data/raw --out data/processed

Notes that matter for analysis:
  * FSIS writes missing values as the string "NULL" and the JSON contains bare
    NaN tokens. Python's json module accepts NaN; strict parsers do not.
  * "routine" samples (project codes HC_*) are the only ones FSIS uses for the
    Salmonella performance categories. Follow-up (F_*) and exploratory or
    special projects are targeted and must not be pooled into prevalence.
  * FSIS states these data must not be used to link samples to outbreaks or to
    each other. Treat them as process-control evidence only.
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

NULLS = {"NULL", "", "None", "nan", "NaN"}

# project_code -> (product_class, program)
PROJECT_MAP = {
    "HC_CH_CARC01": ("chicken_carcass", "routine"),
    "HC_TU_CARC01": ("turkey_carcass", "routine"),
    "HC_CH_COM01": ("comminuted_chicken", "routine"),
    "HC_TU_COM01": ("comminuted_turkey", "routine"),
    "HC_CPT_LBW01": ("chicken_parts", "routine"),
    "F_CH_CARC01": ("chicken_carcass", "followup"),
    "F_TU_CARC01": ("turkey_carcass", "followup"),
    "F_CH_COM01": ("comminuted_chicken", "followup"),
    "F_TU_COM01": ("comminuted_turkey", "followup"),
    "F_CPT_LBW01": ("chicken_parts", "followup"),
    "EX_CHCAR_RH1": ("chicken_carcass_rehang", "exploratory"),
    "NRTE_EXP_CH": ("comminuted_chicken", "exploratory"),
    "NRTE_EXP_TU": ("comminuted_turkey", "exploratory"),
    "EXP_CH_MSK01": ("msk_chicken", "exploratory"),
    "EXP_TU_MSK01": ("msk_turkey", "exploratory"),
    "EXP_CPT_QH01": ("chicken_parts_quarter_half", "exploratory"),
    "EXP_CPT_OT01": ("chicken_parts_other", "exploratory"),
    "RE_CH_CARC01": ("chicken_carcass", "religious_exempt"),
    "LO_CH_CARC01": ("chicken_carcass", "low_volume"),
    "LO_TU_CARC01": ("turkey_carcass", "low_volume"),
    "LO_CH_COM01": ("comminuted_chicken", "low_volume"),
    "LO_TU_COM01": ("comminuted_turkey", "low_volume"),
    "LO_CH_MSK01": ("msk_chicken", "low_volume"),
    "LO_TU_MSK01": ("msk_turkey", "low_volume"),
    "LO_CPT_LBW01": ("chicken_parts", "low_volume"),
    "LO_CPT_QH01": ("chicken_parts_quarter_half", "low_volume"),
    "LO_CPT_OT01": ("chicken_parts_other", "low_volume"),
}

# FSIS Directive 10,250.2: (max positives, of n samples, minimum samples to assess)
PERFORMANCE_STANDARDS = {
    "chicken_carcass": (5, 51, 11),
    "turkey_carcass": (4, 56, 14),
    "comminuted_chicken": (13, 52, 10),
    "comminuted_turkey": (7, 52, 10),
    "chicken_parts": (8, 52, 10),
}


# --------------------------------------------------------------------------- helpers
def load_single_json(zip_path: Path):
    """Each FSIS zip holds exactly one JSON file. Returns the parsed object."""
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        if len(names) != 1:
            raise ValueError(f"{zip_path.name}: expected 1 member, found {names}")
        with z.open(names[0]) as fh:
            return json.load(fh), names[0]


def clean_frame(rows: list[dict]) -> pd.DataFrame:
    """List of dicts -> DataFrame with FSIS 'NULL' strings turned into real NA and text stripped."""
    df = pd.DataFrame(rows)
    for c in df.columns:
        if df[c].dtype == object or pd.api.types.is_string_dtype(df[c]):
            s = df[c].map(lambda v: v.strip() if isinstance(v, str) else v)
            df[c] = s.where(~s.isin(NULLS), other=pd.NA)
    return df


def fiscal_year(d: pd.Series) -> pd.Series:
    return (d.dt.year + (d.dt.month >= 10).astype(int)).astype("Int16")


def pos_neg(s: pd.Series) -> pd.Series:
    """'Positive'/'Negative' (any case) -> 1/0, everything else (cancelled, NULL) -> NA."""
    t = s.astype("string").str.strip().str.lower()
    out = pd.Series(pd.NA, index=s.index, dtype="Int8")
    out[t == "positive"] = 1
    out[t == "negative"] = 0
    return out


_num_re = re.compile(r"^\s*([<>]=?)?\s*([0-9]*\.?[0-9]+)\s*$")


def censored_number(s: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Parse lab strings such as '<10', '> 1100', '44' into (value, censor sign)."""
    vals, signs = [], []
    for v in s:
        if v is None or v is pd.NA or (isinstance(v, float) and np.isnan(v)):
            vals.append(np.nan); signs.append(pd.NA); continue
        m = _num_re.match(str(v))
        if not m:
            vals.append(np.nan); signs.append(pd.NA); continue
        vals.append(float(m.group(2))); signs.append(m.group(1) or "=")
    return pd.Series(vals, index=s.index, dtype="float64"), pd.Series(signs, index=s.index, dtype="string")


# --------------------------------------------------------------------------- raw poultry
def build_poultry(raw: Path, out: Path, report: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    prim, sec = [], []
    files = sorted((raw / "raw_poultry").glob("raw_poultry_sampling_data_fy*.zip"))
    if not files:
        raise FileNotFoundError("no raw_poultry zips found")
    last_meta = None
    for zp in files:
        fy_file = int(re.search(r"fy(\d{4})", zp.name).group(1))
        obj, member = load_single_json(zp)
        top = obj[0]
        meta, data = top["metadata"], top["data"]
        p = clean_frame(data["primary_table_data"]); s = clean_frame(data["secondary_table_data"])
        p["fy_file"] = fy_file; s["fy_file"] = fy_file
        rec = meta.get("data_records", {})
        report["raw_poultry"][fy_file] = {
            "member": member, "created": meta.get("creation_date"),
            "primary_rows": len(p), "secondary_rows": len(s),
            "metadata_primary": rec.get("primary"), "metadata_secondary": rec.get("secondary"),
            "rows_match_metadata": bool(len(p) == rec.get("primary") and len(s) == rec.get("secondary")),
        }
        prim.append(p); sec.append(s); last_meta = (fy_file, meta)
        del obj, top, data
    P = pd.concat(prim, ignore_index=True); S = pd.concat(sec, ignore_index=True)

    # ---- samples (primary)
    P["collection_date"] = pd.to_datetime(P["collection_date"], errors="coerce")
    P["fy"] = fiscal_year(P["collection_date"])
    P["form_id"] = P["form_id"].astype("string")
    P["establishment_id"] = P["establishment_id"].astype("Int32")
    P["sample_number"] = P["sample_number"].astype("Int64")
    pm = P["project_code"].map(PROJECT_MAP)
    P["product_class"] = pm.map(lambda t: t[0] if isinstance(t, tuple) else "special")
    P["program"] = pm.map(lambda t: t[1] if isinstance(t, tuple) else "special")
    P["species"] = np.where(P["project_code"].str.contains("TU", na=False), "turkey", "chicken")
    P["sal_result"] = pos_neg(P["salmonella_sp_analysis"])
    c30, c1 = pos_neg(P["campylobacter_analysis_30ml"]), pos_neg(P["campylobacter_analysis_1ml"])
    P["campy_result"] = c30.where(c30.notna(), c1)
    P["campy_method"] = pd.Series(np.where(c30.notna(), "30ml_enrichment", np.where(c1.notna(), "1ml_direct", None)), dtype="string")
    # Salmonella enumeration (PCR, CFU) is reported per g or per mL depending on the product
    g_val, g_sign = censored_number(P["salmonella_quantitative_cfu_g"])
    m_val, m_sign = censored_number(P["salmonella_quantitative_cfu_ml"])
    P["sal_cfu"] = g_val.where(g_sign.notna(), m_val)
    P["sal_cfu_sign"] = g_sign.where(g_sign.notna(), m_sign)
    P["sal_cfu_unit"] = pd.Series(np.where(g_sign.notna(), "g", np.where(m_sign.notna(), "ml", None)), dtype="string")
    has_cfu = P["sal_cfu_sign"].notna()
    ge10 = pd.Series(pd.NA, index=P.index, dtype="boolean")
    ge10[has_cfu] = ((P.loc[has_cfu, "sal_cfu_sign"] != "<") & (P.loc[has_cfu, "sal_cfu"] >= 10)).astype(bool).to_numpy()
    P["sal_cfu_ge10"] = ge10
    for src, name in [("aerobic_plate_count_mpn_ml", "apc_ml"), ("enterobacteriaceae_mpn_ml", "eb_ml")]:
        v, sg = censored_number(P[src]); P[name] = v; P[name + "_sign"] = sg
    keep = ["form_id", "sample_number", "establishment_id", "establishment_number", "establishment_name", "establishment_state",
            "project_code", "project_name", "product_class", "program", "species", "collection_date", "fy", "fy_file",
            "sample_source_name", "product_type", "not_analyzed", "sal_result", "campy_result", "campy_method",
            "sal_cfu", "sal_cfu_sign", "sal_cfu_unit", "sal_cfu_ge10", "apc_ml", "apc_ml_sign", "eb_ml", "eb_ml_sign",
            "salmonella_sp_analysis", "salmonellae_mpn_g", "salmonella_mpn_qualitative"]
    samples = P[keep].sort_values(["collection_date", "form_id"]).reset_index(drop=True)

    # ---- isolates (secondary). One row per isolate; pathogen_number prefix tells the organism.
    S["form_id"] = S["form_id"].astype("string")
    sal_cols = [c for c in S.columns if c.startswith("salmonella_")]
    campy_cols = [c for c in S.columns if c.startswith("campylobacter_")]
    is_sal = S["pathogen_number"].astype("string").str.startswith("SALM", na=False) | S[["salmonella_serotype", "salmonella_sra_accession_number"]].notna().any(axis=1)
    is_campy = S["pathogen_number"].astype("string").str.startswith("CAMP", na=False) | S[["campylobacter_jejuni", "campylobacter_coli"]].notna().any(axis=1)
    report["secondary_split"] = {"rows": int(len(S)), "salmonella": int(is_sal.sum()), "campylobacter": int(is_campy.sum()),
                                 "both": int((is_sal & is_campy).sum()), "neither": int((~is_sal & ~is_campy).sum())}
    base = ["form_id", "fsis_number", "pathogen_number", "fy_file"]
    sal = S.loc[is_sal, base + sal_cols].copy(); campy = S.loc[is_campy, base + campy_cols].copy()
    sal.columns = [c.replace("salmonella_", "") for c in sal.columns]
    campy.columns = [c.replace("campylobacter_", "") for c in campy.columns]
    for df in (sal, campy):
        df["sequenced"] = df["sra_accession_number"].notna()
        for c in [c for c in df.columns if c.endswith("_mic")]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        for c in [c for c in df.columns if c.endswith("_resistant_ast") or c.endswith("_resistant_wgs")]:
            df[c] = df[c].astype("string").str.lower().map({"yes": True, "no": False}).astype("boolean")
    not_char = sal["serotype"].astype("string").str.contains("characterization not available", case=False, na=False)
    sal["serotype_clean"] = sal["serotype"].where(~not_char, pd.NA)
    sal["vaccine_strain"] = sal["serotype"].astype("string").str.contains("vaccine", case=False, na=False)
    # attach sample context
    ctx = samples[["form_id", "establishment_id", "establishment_state", "collection_date", "fy", "project_code", "product_class", "program", "species"]]
    dup_forms = int(ctx["form_id"].duplicated().sum())
    report["duplicate_form_ids_in_samples"] = dup_forms
    ctx = ctx.drop_duplicates("form_id")
    sal = sal.merge(ctx, on="form_id", how="left", validate="m:1")
    campy = campy.merge(ctx, on="form_id", how="left", validate="m:1")
    report["orphan_isolates"] = {"salmonella": int(sal["establishment_id"].isna().sum()), "campylobacter": int(campy["establishment_id"].isna().sum())}
    # FSIS does not count positives typed as a possible vaccine strain when it assigns performance categories.
    # sal_result_cat is the result as FSIS counts it for categories (checked in 04_validate_categories.py).
    vac_only = sal.groupby("form_id")["vaccine_strain"].all()
    samples["sal_vaccine_only"] = (samples["form_id"].map(vac_only).fillna(False).astype(bool) & (samples["sal_result"] == 1).fillna(False)).astype(bool)
    samples["sal_result_cat"] = samples["sal_result"].where(~samples["sal_vaccine_only"], 0)
    report["vaccine_only_positives"] = int(samples["sal_vaccine_only"].sum())

    # ---- documentation shipped inside the newest file
    fy_meta, meta = last_meta
    pd.DataFrame(meta["data_dictionary"]["primary"]).to_csv(out / "data_dictionary_primary.csv", index=False)
    pd.DataFrame(meta["data_dictionary"]["secondary"]).to_csv(out / "data_dictionary_secondary.csv", index=False)
    pd.DataFrame(meta["project_codes"]["project_code_table"]).to_csv(out / "project_codes.csv", index=False)
    pd.DataFrame(meta["mic_thresholds"]).to_csv(out / "mic_thresholds.csv", index=False)
    pd.DataFrame(meta["fda_antimicrobial_classification"]["fda_antimicrobial_drug_classification_table"]).to_csv(out / "fda_antimicrobial_classes.csv", index=False)
    (out / f"fsis_metadata_fy{fy_meta}.json").write_text(json.dumps({k: v for k, v in meta.items() if k not in ("data_dictionary", "mic_thresholds")}, indent=1, default=str))
    return samples, sal, campy


# --------------------------------------------------------------------------- NARMS cecal
CECAL_CORE = ["establishment_id", "establishment_number", "establishment_name", "establishment_state", "project_code", "project_name",
              "slaughter_class", "form_id", "collection_date", "salmonella_sp", "salmonella_molecular_serotype", "salmonella_fsis_number",
              "salmonella_sra_accession_number", "campylobacter", "campylobacter_coli", "campylobacter_jejuni", "campylobacter_lari",
              "campylobacter_sra_accession_number", "e_coli", "e_coli_sra_accession_number", "enterococcus", "enterococcus_species",
              "enterococcus_sra_accession_number"]


def build_cecal(raw: Path, report: dict) -> pd.DataFrame:
    frames = []
    for zp in sorted((raw / "narms_cecal").glob("fsis_narms_cecal_sampling_fy*.zip")):
        fy_file = int(re.search(r"fy(\d{4})", zp.name).group(1))
        obj, member = load_single_json(zp)
        top = obj[0] if isinstance(obj, list) else obj
        rows = top["data"] if isinstance(top["data"], list) else next(iter(top["data"].values()))
        df = clean_frame(rows)
        n_cols = df.shape[1]
        missing = [c for c in CECAL_CORE if c not in df.columns]
        for c in missing:
            df[c] = pd.NA
        # keep core columns plus genotype strings when present (AST panels stay in the raw file)
        extra = [c for c in df.columns if c.endswith("_resistance_genotype") or c.endswith("_virulence_genotype")]
        df = df[CECAL_CORE + extra].copy(); df["fy_file"] = fy_file
        report["narms_cecal"][fy_file] = {"member": member, "rows": len(df), "metadata_rows": top["metadata"].get("data_records"),
                                          "raw_columns": n_cols, "core_missing": missing}
        frames.append(df); del obj, top, rows
    C = pd.concat(frames, ignore_index=True)
    C["collection_date"] = pd.to_datetime(C["collection_date"], errors="coerce")
    C["fy"] = fiscal_year(C["collection_date"])
    C["establishment_id"] = pd.to_numeric(C["establishment_id"], errors="coerce").astype("Int32")
    C["form_id"] = C["form_id"].astype("string")
    for c in ["salmonella_sp", "campylobacter", "e_coli", "enterococcus"]:
        C[c + "_result"] = pos_neg(C[c])
    return C


# --------------------------------------------------------------------------- establishments
def build_establishments(raw: Path, report: dict) -> pd.DataFrame:
    e = raw / "establishments"
    rd = lambda n: pd.read_csv(e / n, dtype=str, encoding="utf-8-sig")
    active = rd("MPI_Directory_by_Establishment_Number.csv"); active["active"] = True
    inactive = rd("MPI_Inactive_Directory_by_Establishment_Number.csv").rename(columns={"earliest_grant_date": "grant_date"}); inactive["active"] = False
    demo = rd("Dataset_Establishment_Demographic_Data.csv")
    keep_demo = ["establishment_id", "active_poultry_grant", "inspection_system_npis", "inspection_system_npis_waiver",
                 "poultry_exemption_religious", "slaughter", "processing", "processing_volume_category", "slaughter_volume_category",
                 "young_chicken_slaughter", "young_turkey_slaughter", "raw_intact_poultry_processing", "raw_non_intact_poultry_processing",
                 "rte_poultry_processing", "nrte_poultry_processing", "category_start_date", "category_end_date",
                 "young_chicken_carcasses_category", "young_turkey_carcasses_category", "comminuted_chicken_category",
                 "comminuted_turkey_category", "chicken_parts_category"]
    keep_demo = [c for c in keep_demo if c in demo.columns]
    E = pd.concat([active, inactive], ignore_index=True)
    report["establishments"] = {"active": int(len(active)), "inactive": int(len(inactive)), "demographic_rows": int(len(demo)),
                                "duplicate_ids": int(E["establishment_id"].duplicated().sum())}
    E = E.drop_duplicates("establishment_id", keep="first").merge(demo[keep_demo], on="establishment_id", how="left")
    E["establishment_id"] = E["establishment_id"].astype("Int32")
    for c in ["latitude", "longitude", "processing_volume_category", "slaughter_volume_category"]:
        if c in E: E[c] = pd.to_numeric(E[c], errors="coerce")
    E["haccp_size"] = E["size"].replace({"N / A": pd.NA})
    for c in ["grant_date", "inactive_effective_date", "category_start_date", "category_end_date"]:
        if c in E: E[c] = pd.to_datetime(E[c], errors="coerce")
    yes = lambda s: s.astype("string").str.lower().eq("yes").fillna(False)
    for c in [c for c in keep_demo if c not in ("establishment_id", "processing_volume_category", "slaughter_volume_category", "category_start_date", "category_end_date") and not c.endswith("_category")]:
        E[c] = yes(E[c])
    # crude corporate grouping from the name on the grant (first two words, upper-cased)
    E["company_key"] = E["establishment_name"].astype("string").str.upper().str.replace(r"[^A-Z0-9 ]", "", regex=True).str.split().str[:2].str.join(" ")
    return E.drop(columns=["phone", "street"], errors="ignore")


def build_posted_categories(raw: Path) -> pd.DataFrame:
    """FSIS monthly posting: establishment number, name, city, state, district, product class, category."""
    std = {"establishmentnumber": "establishment_number", "establishmentname": "establishment_name", "city": "city", "state": "state",
           "districtnumber": "district", "productclass": "product_class_posted", "category": "category", "salmcat": "category"}
    frames = []
    for xp in sorted((raw / "salmonella_categories").glob("Dataset_EstablishmentCategories_2*.xlsx")):
        rawdf = pd.read_excel(xp, header=None, dtype=str)
        norm = rawdf.iloc[:, 0].astype("string").str.replace(" ", "").str.lower()
        hi = int(norm[norm.str.startswith("establishmentnumber", na=False)].index[0])
        window = next((str(v) for v in rawdf.iloc[:hi, 0] if isinstance(v, str) and "through" in v.lower()), "")
        df = rawdf.iloc[hi + 1:].copy()
        df.columns = [std.get(str(c).replace(" ", "").strip().lower(), str(c)) for c in rawdf.iloc[hi]]
        df = df[df["establishment_number"].notna()].reset_index(drop=True)
        df["category"] = df["category"].fillna("NA").str.strip()
        df["window_text"] = window; df["source_file"] = xp.name
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def build_posted_aggregate(raw: Path) -> pd.DataFrame:
    """FSIS aggregate posting: number of establishments in each category, by product class and HACCP size."""
    rows = []
    for xp in sorted((raw / "salmonella_categories").glob("Dataset_EstablishmentCategoriesAggregate_2*.xlsx")):
        for sheet, df in pd.read_excel(xp, sheet_name=None, header=None, dtype=str).items():
            window = next((str(v) for v in df.iloc[:, 0] if isinstance(v, str) and "through" in v.lower()), "")
            hdr = df.index[df.iloc[:, 1].astype("string").str.contains("All Establishments Number", na=False)]
            if len(hdr) == 0:
                continue
            body = df.loc[hdr[0] + 1:]
            for _, r in body.iterrows():
                label = str(r.iloc[0]).strip()
                if not label.startswith("Category"):
                    continue
                for j, grp in zip((1, 3, 5, 7), ("All", "Large", "Small", "Very Small")):
                    rows.append({"product_class_posted": sheet, "category": label.replace("Category ", ""), "haccp_size": grp,
                                 "establishments": int(float(r.iloc[j])), "percent": float(r.iloc[j + 1]), "window_text": window, "source_file": xp.name})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    report: dict = {"raw_poultry": {}, "narms_cecal": {}}
    samples, sal, campy = build_poultry(a.raw, a.out, report)
    cecal = build_cecal(a.raw, report)
    est = build_establishments(a.raw, report)
    posted = build_posted_categories(a.raw)
    posted_agg = build_posted_aggregate(a.raw)
    known = set(est["establishment_id"].dropna().astype(int))
    report["join_checks"] = {
        "sample_establishments": int(samples["establishment_id"].nunique()),
        "sample_establishments_in_directory": int(samples.loc[samples["establishment_id"].isin(known), "establishment_id"].nunique()),
        "samples_with_directory_match_pct": round(100 * float(samples["establishment_id"].isin(known).mean()), 2),
        "samples_fy2024plus_with_directory_match_pct": round(100 * float(samples.loc[samples["fy"] >= 2024, "establishment_id"].isin(known).mean()), 2),
    }
    report["totals"] = {"samples": int(len(samples)), "sal_tested": int(samples["sal_result"].notna().sum()), "sal_positive": int(samples["sal_result"].sum()),
                        "sal_isolates": int(len(sal)), "campy_isolates": int(len(campy)), "cecal_samples": int(len(cecal)),
                        "establishments": int(len(est)), "posted_category_rows": int(len(posted)),
                        "date_min": str(samples["collection_date"].min().date()), "date_max": str(samples["collection_date"].max().date())}
    for name, df in [("samples", samples), ("sal_isolates", sal), ("campy_isolates", campy), ("cecal", cecal), ("establishments", est),
                     ("posted_categories", posted), ("posted_aggregate", posted_agg)]:
        df.to_parquet(a.out / f"{name}.parquet", index=False)
    (a.out / "build_report.json").write_text(json.dumps(report, indent=1, default=str))
    print(json.dumps({k: report[k] for k in ("totals", "join_checks", "secondary_split", "orphan_isolates", "duplicate_form_ids_in_samples", "vaccine_only_positives", "establishments")}, indent=1))
    bad = [fy for fy, r in report["raw_poultry"].items() if not r["rows_match_metadata"]]
    print("fiscal years whose row counts differ from FSIS metadata:", bad or "none")


if __name__ == "__main__":
    main()
