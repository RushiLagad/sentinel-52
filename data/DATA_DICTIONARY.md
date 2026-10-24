# Data dictionary

Generated from the built tables by `analysis/scripts/02_build_tables.py`. Field descriptions marked *(FSIS)* are taken verbatim from the data dictionary FSIS ships inside the raw sampling files. Fields marked *(derived)* are created by this project and are described here, not by FSIS.

Source, licence and collection details for every dataset are in `PROVENANCE.md`. Long FSIS descriptions are truncated here; the complete text ships in `data_dictionary_primary.csv` and `data_dictionary_secondary.csv`, and the project-code lookup in `project_codes.csv`.


## `samples.parquet`

One row per laboratory sample. The analysis backbone.

Rows: 325,123  |  Columns: 33

| Column | Type | Non-null | Description |
|---|---|---|---|
| `form_id` | string | 100% | The form number used to uniquely identify a specific sample. *(FSIS)* |
| `sample_number` | Int64 | 100% | The number used to uniquely identify a sample within the form_id. A single form_id can have multiple sample numbers depending on the types of tests performed. *(FSIS)* |
| `establishment_id` | Int32 | 100% | Derived. Establishment number normalised for joining to the MPI directory. *(derived)* |
| `establishment_number` | str | 100% | A letter/number combination identifying each establishment. Establishment numbers may be reused over time; therefore, we recommend relying on the establishment_id to merge data from different datasets. Please note that other FSIS datasets may represent this variable as EstablishmentNumber with capital letters and … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* |
| `establishment_name` | str | 100% | The name of an establishment on its FSIS grant of inspection. *(FSIS)* |
| `establishment_state` | str | 100% | The state where the establishment is located. *(FSIS)* |
| `project_code` | str | 100% | A short name given to easily identify an FSIS sampling project. *(FSIS)* |
| `project_name` | str | 100% | The name of the FSIS sampling project. *(FSIS)* |
| `product_class` | str | 100% | Derived. Product category implied by project_code: chicken_carcass, chicken_parts, comminuted_chicken, turkey_carcass, comminuted_turkey, or an exploratory class. *(derived)* |
| `program` | str | 100% | Derived. Sampling programme implied by project_code: routine (HC_*), followup (F_*), exploratory, special, low_volume or religious_exempt. *(derived)* |
| `species` | str | 100% | Derived. chicken or turkey, from product_class. *(derived)* |
| `collection_date` | datetime64[us] | 100% | The date the FSIS inspector collected the sample at the FSIS-regulated establishment. *(FSIS)* |
| `fy` | Int16 | 100% | Derived. Federal fiscal year of collection_date (Oct 1 to Sep 30). *(derived)* |
| `fy_file` | int64 | 100% | Derived. Fiscal-year file the record was read from. *(derived)* |
| `sample_source_name` | str | 100% | The animal or product from which the sample was obtained. *(FSIS)* |
| `product_type` | str | 52% | The specific part type collected, as entered by the inspection personnel collecting the sample (e.g., leg, quarter-carcass, livers, gizzards, hearts, and necks). This field is only applicable for the following projects: EXP_CPT_OT01 EXP_CPT_QH01 F_CH_COM01 F_CPT_LBW01 F_TU_COM01 HC_CH_COM01 HC_CPT_LBW01 HC_TU_COM01 … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* |
| `not_analyzed` | str | 100% | Indicates if the corresponding sample was unable to be analyzed. A value of '00' indicates the sample was analyzed. *(FSIS)* |
| `sal_result` | Int8 | 100% | Derived. 1 if salmonella_sp_analysis is Positive, 0 if Negative, null otherwise. *(derived)* |
| `campy_result` | Int8 | 82% | Derived. 1/0 from the 1 mL or 30 mL Campylobacter analysis, whichever was run. *(derived)* |
| `campy_method` | string | 82% | Derived. Which Campylobacter analysis produced campy_result (1ml or 30ml). *(derived)* |
| `sal_cfu` | float64 | 3% | Derived. Numeric part of the Salmonella enumeration result. Every reported value is either '<10' or a number of 10 or more. *(derived)* |
| `sal_cfu_sign` | string | 3% | Derived. Censoring operator parsed from the enumeration string: '<' or '='. *(derived)* |
| `sal_cfu_unit` | string | 3% | Derived. ml (carcass and parts rinsate) or g (comminuted product). *(derived)* |
| `sal_cfu_ge10` | boolean | 3% | Derived. True when the sample was enumerated at 10 CFU or more, i.e. quantifiable rather than '<10'. Null when no count was reported. *(derived)* |
| `apc_ml` | float64 | 6% | Derived. Numeric aerobic plate count per mL. *(derived)* |
| `apc_ml_sign` | string | 6% | Derived. Censoring operator for apc_ml. *(derived)* |
| `eb_ml` | float64 | 3% | Derived. Numeric Enterobacteriaceae count per mL. *(derived)* |
| `eb_ml_sign` | string | 3% | Derived. Censoring operator for eb_ml. *(derived)* |
| `salmonella_sp_analysis` | str | 100% | Microbiology Test: The result of the analysis for Salmonella in the sample. Negative indicates Salmonella was not found in the sample. Positive indicates Salmonella was found in the sample. *(FSIS)* |
| `salmonellae_mpn_g` | str | 1% | Microbiology Test (Unit: per gram) - Result of the analysis to estimate the population density of viable Salmonella. Results are reported as an estimate of the most probable number (MPN/g) of observed positive growth responses in a standard dilution series of sample inoculum. Salmonella MPN was discontinued in … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* |
| `salmonella_mpn_qualitative` | str | 1% | Microbiology Test: Qualitative result of the analysis to estimate the population density of viable Salmonella. Salmonella most probable number (MPN) was discontinued in March 2020. Positive = observed growth responses in at least one culture tube of a standard dilution series of the sample inoculum. Negative = no … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* |
| `sal_vaccine_only` | bool | 100% | Derived. True when the only Salmonella isolate for the sample is typed 'Possible Vaccine Strain'. *(derived)* |
| `sal_result_cat` | Int8 | 100% | Derived. As sal_result, but positives typed as a possible vaccine strain are set to 0. This is how FSIS counts for categorisation from 1 April 2024. *(derived)* |

## `sal_isolates.parquet`

One row per Salmonella isolate recovered, with serotype, sequence identifiers, resistance genotype and FSIS sequence-based resistance calls.

Rows: 37,695  |  Columns: 96

| Column | Type | Non-null | Description |
|---|---|---|---|
| `form_id` | string | 100% | The form number used to uniquely identify a specific sample. *(FSIS)* |
| `fsis_number` | str | 81% | The FSIS number is a unique identifier for retrieving whole genome sequence data from the National Center for Biotechnology and Information (NCBI) Pathogen Detection Isolates Browser (https://www.ncbi.nlm.nih.gov/pathogens/isolates/). NCBI developed the Browser to help users learn about the sequences they … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* |
| `pathogen_number` | str | 100% | A combination of the pathogen and the primary sample number. The primary sample number is known as the 'sample_number' in the primary dataset. The pathogen is indicated by a four-letter code: SALM: Salmonella O157: E. coli O157:H7 ECOL: Generic E. coli STEC: Shiga toxin-producing E. coli of all O-groups LMON: … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* |
| `fy_file` | int64 | 100% | Derived. Fiscal-year file the record was read from. *(derived)* |
| `allele_code_version` | str | 61% | *(derived; see build script)* |
| `allele_code` | str | 61% | *(derived; see build script)* |
| `allele_code_date` | str | 61% | *(derived; see build script)* |
| `sra_accession_number` | str | 81% | *(derived; see build script)* |
| `bio_sample_accession_number` | str | 81% | *(derived; see build script)* |
| `bio_project_number` | str | 81% | *(derived; see build script)* |
| `multi_locus_sequence` | str | 49% | *(derived; see build script)* |
| `resistance_genotype` | str | 62% | *(derived; see build script)* |
| `stress_genotype` | str | 62% | *(derived; see build script)* |
| `virulence_genotype` | str | 59% | *(derived; see build script)* |
| `serotype` | str | 100% | *(derived; see build script)* |
| `primary_pfge_pattern` | str | 39% | *(derived; see build script)* |
| `secondary_pfge_pattern` | str | 39% | *(derived; see build script)* |
| `ampicillin_operator` | str | 74% | *(derived; see build script)* |
| `ampicillin_mic` | float64 | 74% | *(derived; see build script)* |
| `ampicillin_resistant_ast` | boolean | 74% | *(derived; see build script)* |
| `amoxicillin_clavulanic_acid_operator` | str | 74% | *(derived; see build script)* |
| `amoxicillin_clavulanic_acid_mic` | float64 | 74% | *(derived; see build script)* |
| `amoxicillin_clavulanic_acid_resistant_ast` | boolean | 74% | *(derived; see build script)* |
| `ceftriaxone_operator` | str | 74% | *(derived; see build script)* |
| `ceftriaxone_mic` | float64 | 74% | *(derived; see build script)* |
| `ceftriaxone_resistant_ast` | boolean | 74% | *(derived; see build script)* |
| `azithromycin_operator` | str | 74% | *(derived; see build script)* |
| `azithromycin_mic` | float64 | 74% | *(derived; see build script)* |
| `azithromycin_resistant_ast` | boolean | 74% | *(derived; see build script)* |
| `chloramphenicol_operator` | str | 74% | *(derived; see build script)* |
| `chloramphenicol_mic` | float64 | 74% | *(derived; see build script)* |
| `chloramphenicol_resistant_ast` | boolean | 74% | *(derived; see build script)* |
| `ciprofloxacin_operator` | str | 74% | *(derived; see build script)* |
| `ciprofloxacin_mic` | float64 | 74% | *(derived; see build script)* |
| `ciprofloxacin_resistant_ast` | boolean | 74% | *(derived; see build script)* |
| `colistin_operator` | str | 28% | *(derived; see build script)* |
| `colistin_mic` | float64 | 28% | *(derived; see build script)* |
| `colistin_resistant_ast` | boolean | 28% | *(derived; see build script)* |
| `trimethoprim_sulfamethoxazole_operator` | str | 74% | *(derived; see build script)* |
| `trimethoprim_sulfamethoxazole_mic` | float64 | 74% | *(derived; see build script)* |
| `trimethoprim_sulfamethoxazole_resistant_ast` | boolean | 74% | *(derived; see build script)* |
| `cefoxitin_operator` | str | 74% | *(derived; see build script)* |
| `cefoxitin_mic` | float64 | 74% | *(derived; see build script)* |
| `cefoxitin_resistant_ast` | boolean | 74% | *(derived; see build script)* |
| `gentamicin_operator` | str | 74% | *(derived; see build script)* |
| `gentamicin_mic` | float64 | 74% | *(derived; see build script)* |
| `gentamicin_resistant_ast` | boolean | 74% | *(derived; see build script)* |
| `kanamycin_operator` | str | 2% | *(derived; see build script)* |
| `kanamycin_mic` | float64 | 2% | *(derived; see build script)* |
| `kanamycin_resistant_ast` | boolean | 2% | *(derived; see build script)* |
| `meropenem_operator` | str | 60% | *(derived; see build script)* |
| `meropenem_mic` | float64 | 60% | *(derived; see build script)* |
| `meropenem_resistant_ast` | boolean | 60% | *(derived; see build script)* |
| `nalidixic_acid_operator` | str | 74% | *(derived; see build script)* |
| `nalidixic_acid_mic` | float64 | 74% | *(derived; see build script)* |
| `nalidixic_acid_resistant_ast` | boolean | 74% | *(derived; see build script)* |
| `sulfisoxazole_operator` | str | 74% | *(derived; see build script)* |
| `sulfisoxazole_mic` | float64 | 74% | *(derived; see build script)* |
| `sulfisoxazole_resistant_ast` | boolean | 74% | *(derived; see build script)* |
| `streptomycin_operator` | str | 46% | *(derived; see build script)* |
| `streptomycin_mic` | float64 | 46% | *(derived; see build script)* |
| `streptomycin_resistant_ast` | boolean | 46% | *(derived; see build script)* |
| `tetracycline_operator` | str | 74% | *(derived; see build script)* |
| `tetracycline_mic` | float64 | 74% | *(derived; see build script)* |
| `tetracycline_resistant_ast` | boolean | 74% | *(derived; see build script)* |
| `ceftiofur_operator` | str | 15% | *(derived; see build script)* |
| `ceftiofur_mic` | float64 | 15% | *(derived; see build script)* |
| `ceftiofur_resistant_ast` | boolean | 15% | *(derived; see build script)* |
| `ampicillin_resistant_wgs` | boolean | 19% | *(derived; see build script)* |
| `amoxicillin_clavulanic_acid_resistant_wgs` | boolean | 19% | *(derived; see build script)* |
| `ceftriaxone_resistant_wgs` | boolean | 19% | *(derived; see build script)* |
| `azithromycin_resistant_wgs` | boolean | 19% | *(derived; see build script)* |
| `chloramphenicol_resistant_wgs` | boolean | 19% | *(derived; see build script)* |
| `ciprofloxacin_resistant_wgs` | boolean | 19% | *(derived; see build script)* |
| `colistin_resistant_wgs` | boolean | 19% | *(derived; see build script)* |
| `trimethoprim_sulfamethoxazole_resistant_wgs` | boolean | 19% | *(derived; see build script)* |
| `cefoxitin_resistant_wgs` | boolean | 19% | *(derived; see build script)* |
| `gentamicin_resistant_wgs` | boolean | 19% | *(derived; see build script)* |
| `kanamycin_resistant_wgs` | boolean | 19% | *(derived; see build script)* |
| `meropenem_resistant_wgs` | boolean | 19% | *(derived; see build script)* |
| `nalidixic_acid_resistant_wgs` | boolean | 19% | *(derived; see build script)* |
| `sulfisoxazole_resistant_wgs` | boolean | 19% | *(derived; see build script)* |
| `streptomycin_resistant_wgs` | boolean | 19% | *(derived; see build script)* |
| `tetracycline_resistant_wgs` | boolean | 19% | *(derived; see build script)* |
| `ceftiofur_resistant_wgs` | boolean | 19% | *(derived; see build script)* |
| `sequenced` | bool | 100% | Derived. True when the isolate has an SRA accession. *(derived)* |
| `serotype_clean` | str | 100% | Derived. Serotype with whitespace and case normalised; 'Possible Vaccine Strain' suffix preserved. *(derived)* |
| `vaccine_strain` | boolean | 100% | Derived. True when serotype is typed as a possible vaccine strain. *(derived)* |
| `establishment_id` | Int32 | 100% | Derived. Establishment number normalised for joining to the MPI directory. *(derived)* |
| `establishment_state` | str | 100% | The state where the establishment is located. *(FSIS)* |
| `collection_date` | datetime64[us] | 100% | The date the FSIS inspector collected the sample at the FSIS-regulated establishment. *(FSIS)* |
| `fy` | Int16 | 100% | Derived. Federal fiscal year of collection_date (Oct 1 to Sep 30). *(derived)* |
| `project_code` | str | 100% | A short name given to easily identify an FSIS sampling project. *(FSIS)* |
| `product_class` | str | 100% | Derived. Product category implied by project_code: chicken_carcass, chicken_parts, comminuted_chicken, turkey_carcass, comminuted_turkey, or an exploratory class. *(derived)* |
| `program` | str | 100% | Derived. Sampling programme implied by project_code: routine (HC_*), followup (F_*), exploratory, special, low_volume or religious_exempt. *(derived)* |
| `species` | str | 100% | Derived. chicken or turkey, from product_class. *(derived)* |

## `campy_isolates.parquet`

One row per Campylobacter isolate recovered.

Rows: 35,662  |  Columns: 68

| Column | Type | Non-null | Description |
|---|---|---|---|
| `form_id` | string | 100% | The form number used to uniquely identify a specific sample. *(FSIS)* |
| `fsis_number` | str | 94% | The FSIS number is a unique identifier for retrieving whole genome sequence data from the National Center for Biotechnology and Information (NCBI) Pathogen Detection Isolates Browser (https://www.ncbi.nlm.nih.gov/pathogens/isolates/). NCBI developed the Browser to help users learn about the sequences they … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* |
| `pathogen_number` | str | 100% | A combination of the pathogen and the primary sample number. The primary sample number is known as the 'sample_number' in the primary dataset. The pathogen is indicated by a four-letter code: SALM: Salmonella O157: E. coli O157:H7 ECOL: Generic E. coli STEC: Shiga toxin-producing E. coli of all O-groups LMON: … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* |
| `fy_file` | int64 | 100% | Derived. Fiscal-year file the record was read from. *(derived)* |
| `allele_code_version` | str | 70% | *(derived; see build script)* |
| `allele_code` | str | 67% | *(derived; see build script)* |
| `allele_code_date` | str | 70% | *(derived; see build script)* |
| `sra_accession_number` | str | 94% | *(derived; see build script)* |
| `bio_sample_accession_number` | str | 94% | *(derived; see build script)* |
| `bio_project_number` | str | 94% | *(derived; see build script)* |
| `multi_locus_sequence` | str | 0% | *(derived; see build script)* |
| `resistance_genotype` | str | 62% | *(derived; see build script)* |
| `stress_genotype` | str | 48% | *(derived; see build script)* |
| `virulence_genotype` | str | 0% | *(derived; see build script)* |
| `jejuni` | str | 100% | *(derived; see build script)* |
| `coli` | str | 100% | *(derived; see build script)* |
| `lari` | str | 100% | *(derived; see build script)* |
| `primary_pfge_pattern` | str | 14% | *(derived; see build script)* |
| `secondary_pfge_pattern` | str | 14% | *(derived; see build script)* |
| `azithromycin_operator` | str | 79% | *(derived; see build script)* |
| `azithromycin_mic` | float64 | 79% | *(derived; see build script)* |
| `azithromycin_resistant_ast` | boolean | 79% | *(derived; see build script)* |
| `ciprofloxacin_operator` | str | 79% | *(derived; see build script)* |
| `ciprofloxacin_mic` | float64 | 79% | *(derived; see build script)* |
| `ciprofloxacin_resistant_ast` | boolean | 79% | *(derived; see build script)* |
| `clindamycin_operator` | str | 79% | *(derived; see build script)* |
| `clindamycin_mic` | float64 | 79% | *(derived; see build script)* |
| `clindamycin_resistant_ast` | boolean | 79% | *(derived; see build script)* |
| `erythromycin_operator` | str | 79% | *(derived; see build script)* |
| `erythromycin_mic` | float64 | 79% | *(derived; see build script)* |
| `erythromycin_resistant_ast` | boolean | 79% | *(derived; see build script)* |
| `florfenicol_operator` | str | 79% | *(derived; see build script)* |
| `florfenicol_mic` | float64 | 79% | *(derived; see build script)* |
| `florfenicol_resistant_ast` | boolean | 79% | *(derived; see build script)* |
| `gentamicin_operator` | str | 79% | *(derived; see build script)* |
| `gentamicin_mic` | float64 | 79% | *(derived; see build script)* |
| `gentamicin_resistant_ast` | boolean | 79% | *(derived; see build script)* |
| `meropenem_operator` | str | 51% | *(derived; see build script)* |
| `meropenem_mic` | float64 | 51% | *(derived; see build script)* |
| `meropenem_resistant_ast` | boolean | 51% | *(derived; see build script)* |
| `nalidixic_acid_operator` | str | 79% | *(derived; see build script)* |
| `nalidixic_acid_mic` | float64 | 79% | *(derived; see build script)* |
| `nalidixic_acid_resistant_ast` | boolean | 79% | *(derived; see build script)* |
| `telithromycin_operator` | str | 17% | *(derived; see build script)* |
| `telithromycin_mic` | float64 | 17% | *(derived; see build script)* |
| `telithromycin_resistant_ast` | boolean | 17% | *(derived; see build script)* |
| `tetracycline_operator` | str | 79% | *(derived; see build script)* |
| `tetracycline_mic` | float64 | 79% | *(derived; see build script)* |
| `tetracycline_resistant_ast` | boolean | 79% | *(derived; see build script)* |
| `azithromycin_resistant_wgs` | boolean | 22% | *(derived; see build script)* |
| `ciprofloxacin_resistant_wgs` | boolean | 22% | *(derived; see build script)* |
| `clindamycin_resistant_wgs` | boolean | 22% | *(derived; see build script)* |
| `erythromycin_resistant_wgs` | boolean | 22% | *(derived; see build script)* |
| `florfenicol_resistant_wgs` | boolean | 22% | *(derived; see build script)* |
| `gentamicin_resistant_wgs` | boolean | 22% | *(derived; see build script)* |
| `meropenem_resistant_wgs` | boolean | 22% | *(derived; see build script)* |
| `nalidixic_acid_resistant_wgs` | boolean | 22% | *(derived; see build script)* |
| `telithromycin_resistant_wgs` | boolean | 22% | *(derived; see build script)* |
| `tetracycline_resistant_wgs` | boolean | 22% | *(derived; see build script)* |
| `sequenced` | bool | 100% | Derived. True when the isolate has an SRA accession. *(derived)* |
| `establishment_id` | Int32 | 100% | Derived. Establishment number normalised for joining to the MPI directory. *(derived)* |
| `establishment_state` | str | 100% | The state where the establishment is located. *(FSIS)* |
| `collection_date` | datetime64[us] | 100% | The date the FSIS inspector collected the sample at the FSIS-regulated establishment. *(FSIS)* |
| `fy` | Int16 | 100% | Derived. Federal fiscal year of collection_date (Oct 1 to Sep 30). *(derived)* |
| `project_code` | str | 100% | A short name given to easily identify an FSIS sampling project. *(FSIS)* |
| `product_class` | str | 100% | Derived. Product category implied by project_code: chicken_carcass, chicken_parts, comminuted_chicken, turkey_carcass, comminuted_turkey, or an exploratory class. *(derived)* |
| `program` | str | 100% | Derived. Sampling programme implied by project_code: routine (HC_*), followup (F_*), exploratory, special, low_volume or religious_exempt. *(derived)* |
| `species` | str | 100% | Derived. chicken or turkey, from product_class. *(derived)* |

## `cecal.parquet`

One row per NARMS cecal sample taken at slaughter, covering Salmonella, Campylobacter, E. coli and Enterococcus.

Rows: 72,151  |  Columns: 29

| Column | Type | Non-null | Description |
|---|---|---|---|
| `establishment_id` | Int32 | 100% | Derived. Establishment number normalised for joining to the MPI directory. *(derived)* |
| `establishment_number` | str | 100% | A letter/number combination identifying each establishment. Establishment numbers may be reused over time; therefore, we recommend relying on the establishment_id to merge data from different datasets. Please note that other FSIS datasets may represent this variable as EstablishmentNumber with capital letters and … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* |
| `establishment_name` | str | 100% | The name of an establishment on its FSIS grant of inspection. *(FSIS)* |
| `establishment_state` | str | 100% | The state where the establishment is located. *(FSIS)* |
| `project_code` | str | 100% | A short name given to easily identify an FSIS sampling project. *(FSIS)* |
| `project_name` | str | 100% | The name of the FSIS sampling project. *(FSIS)* |
| `slaughter_class` | str | 100% | *(derived; see build script)* |
| `form_id` | string | 100% | The form number used to uniquely identify a specific sample. *(FSIS)* |
| `collection_date` | datetime64[us] | 100% | The date the FSIS inspector collected the sample at the FSIS-regulated establishment. *(FSIS)* |
| `salmonella_sp` | str | 95% | *(derived; see build script)* |
| `salmonella_molecular_serotype` | str | 23% | *(derived; see build script)* |
| `salmonella_fsis_number` | str | 20% | *(derived; see build script)* |
| `salmonella_sra_accession_number` | str | 20% | A unique identifier for retrieving raw sequencing data and alignment information from the Sequence Read Archive (SRA) from the National Center for Biotechnology and Information (NCBI) database. *(FSIS)* |
| `campylobacter` | str | 77% | *(derived; see build script)* |
| `campylobacter_coli` | str | 27% | Species designation for isolates belonging to the genus Campylobacter. If positive, the species is determined to be coli. *(FSIS)* |
| `campylobacter_jejuni` | str | 27% | Species designation for isolates belonging to the genus Campylobacter. If positive, the species is determined to be jejuni. *(FSIS)* |
| `campylobacter_lari` | str | 27% | Species designation for isolates belonging to the genus Campylobacter. If positive, the species is determined to be lari. *(FSIS)* |
| `campylobacter_sra_accession_number` | str | 22% | A unique identifier for retrieving raw sequencing data and alignment information from the Sequence Read Archive (SRA) from the National Center for Biotechnology and Information (NCBI) database. *(FSIS)* |
| `e_coli` | str | 32% | *(derived; see build script)* |
| `e_coli_sra_accession_number` | str | 13% | *(derived; see build script)* |
| `enterococcus` | str | 32% | *(derived; see build script)* |
| `enterococcus_species` | str | 13% | *(derived; see build script)* |
| `enterococcus_sra_accession_number` | str | 7% | *(derived; see build script)* |
| `fy_file` | int64 | 100% | Derived. Fiscal-year file the record was read from. *(derived)* |
| `fy` | Int16 | 100% | Derived. Federal fiscal year of collection_date (Oct 1 to Sep 30). *(derived)* |
| `salmonella_sp_result` | Int8 | 95% | *(derived; see build script)* |
| `campylobacter_result` | Int8 | 77% | *(derived; see build script)* |
| `e_coli_result` | Int8 | 32% | *(derived; see build script)* |
| `enterococcus_result` | Int8 | 32% | *(derived; see build script)* |

## `establishments.parquet`

One row per establishment in the FSIS Meat, Poultry and Egg Product Inspection Directory, with size, volume categories and location.

Rows: 8,188  |  Columns: 42

| Column | Type | Non-null | Description |
|---|---|---|---|
| `establishment_id` | Int32 | 100% | Derived. Establishment number normalised for joining to the MPI directory. *(derived)* |
| `establishment_number` | str | 100% | A letter/number combination identifying each establishment. Establishment numbers may be reused over time; therefore, we recommend relying on the establishment_id to merge data from different datasets. Please note that other FSIS datasets may represent this variable as EstablishmentNumber with capital letters and … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* |
| `establishment_name` | str | 100% | The name of an establishment on its FSIS grant of inspection. *(FSIS)* |
| `duns_number` | str | 15% | *(derived; see build script)* |
| `city` | str | 100% | *(derived; see build script)* |
| `state` | str | 100% | *(derived; see build script)* |
| `zip` | str | 100% | *(derived; see build script)* |
| `grant_date` | datetime64[us] | 100% | *(derived; see build script)* |
| `activities` | str | 91% | *(derived; see build script)* |
| `dbas` | str | 31% | *(derived; see build script)* |
| `district` | str | 100% | *(derived; see build script)* |
| `circuit` | str | 100% | *(derived; see build script)* |
| `size` | str | 98% | *(derived; see build script)* |
| `latitude` | float64 | 100% | *(derived; see build script)* |
| `longitude` | float64 | 100% | *(derived; see build script)* |
| `county` | str | 100% | *(derived; see build script)* |
| `fips_code` | str | 99% | *(derived; see build script)* |
| `active` | bool | 100% | *(derived; see build script)* |
| `inactive_effective_date` | datetime64[us] | 12% | *(derived; see build script)* |
| `active_poultry_grant` | bool[pyarrow] | 100% | *(derived; see build script)* |
| `inspection_system_npis` | bool[pyarrow] | 100% | *(derived; see build script)* |
| `inspection_system_npis_waiver` | bool[pyarrow] | 100% | *(derived; see build script)* |
| `poultry_exemption_religious` | bool[pyarrow] | 100% | *(derived; see build script)* |
| `slaughter` | bool[pyarrow] | 100% | *(derived; see build script)* |
| `processing` | bool[pyarrow] | 100% | *(derived; see build script)* |
| `processing_volume_category` | float64 | 72% | *(derived; see build script)* |
| `slaughter_volume_category` | float64 | 17% | *(derived; see build script)* |
| `young_chicken_slaughter` | bool[pyarrow] | 100% | *(derived; see build script)* |
| `young_turkey_slaughter` | bool[pyarrow] | 100% | *(derived; see build script)* |
| `raw_intact_poultry_processing` | bool[pyarrow] | 100% | *(derived; see build script)* |
| `raw_non_intact_poultry_processing` | bool[pyarrow] | 100% | *(derived; see build script)* |
| `rte_poultry_processing` | bool[pyarrow] | 100% | *(derived; see build script)* |
| `nrte_poultry_processing` | bool[pyarrow] | 100% | *(derived; see build script)* |
| `category_start_date` | datetime64[us] | 9% | *(derived; see build script)* |
| `category_end_date` | datetime64[us] | 9% | *(derived; see build script)* |
| `young_chicken_carcasses_category` | str | 2% | *(derived; see build script)* |
| `young_turkey_carcasses_category` | str | 0% | *(derived; see build script)* |
| `comminuted_chicken_category` | str | 0% | *(derived; see build script)* |
| `comminuted_turkey_category` | str | 0% | *(derived; see build script)* |
| `chicken_parts_category` | str | 5% | *(derived; see build script)* |
| `haccp_size` | str | 88% | From the FSIS establishment demographic data: Large, Small or Very Small. *(derived)* |
| `company_key` | str | 100% | Derived. Crude two-word normalisation of establishment_name, used only to group plants that appear to share an owner. Not authoritative. *(derived)* |

## `posted_categories.parquet`

FSIS's own published Salmonella category for each establishment and product class, used as ground truth.

Rows: 1,089  |  Columns: 9

| Column | Type | Non-null | Description |
|---|---|---|---|
| `establishment_number` | str | 100% | A letter/number combination identifying each establishment. Establishment numbers may be reused over time; therefore, we recommend relying on the establishment_id to merge data from different datasets. Please note that other FSIS datasets may represent this variable as EstablishmentNumber with capital letters and … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* |
| `establishment_name` | str | 100% | The name of an establishment on its FSIS grant of inspection. *(FSIS)* |
| `city` | str | 100% | *(derived; see build script)* |
| `state` | str | 100% | *(derived; see build script)* |
| `district` | str | 100% | *(derived; see build script)* |
| `product_class_posted` | str | 100% | *(derived; see build script)* |
| `category` | str | 100% | Derived. Rebuilt FSIS Category 1, 2, 3 or NA for the unit at window_end. *(derived)* |
| `window_text` | str | 100% | *(derived; see build script)* |
| `source_file` | str | 100% | *(derived; see build script)* |

## `posted_aggregate.parquet`

FSIS's published category counts by product class and HACCP size.

Rows: 60  |  Columns: 7

| Column | Type | Non-null | Description |
|---|---|---|---|
| `product_class_posted` | str | 100% | *(derived; see build script)* |
| `category` | str | 100% | Derived. Rebuilt FSIS Category 1, 2, 3 or NA for the unit at window_end. *(derived)* |
| `haccp_size` | str | 100% | From the FSIS establishment demographic data: Large, Small or Very Small. *(derived)* |
| `establishments` | int64 | 100% | *(derived; see build script)* |
| `percent` | float64 | 100% | *(derived; see build script)* |
| `window_text` | str | 100% | *(derived; see build script)* |
| `source_file` | str | 100% | *(derived; see build script)* |
