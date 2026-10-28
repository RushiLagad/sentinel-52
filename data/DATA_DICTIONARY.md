# Data dictionary

Every column of every table this project builds. Regenerate with `python scripts/19_build_data_dictionary.py --repo ..` from `analysis/`.

Descriptions marked *(FSIS)* are taken verbatim from the dictionary FSIS ships inside the raw sampling files. Those marked *(FSIS column, described by this project)* are FSIS's columns from source files that carry no dictionary of their own (the MPI directory, the demographic file, the category workbooks and the NARMS cecal files), so the column is FSIS's and the wording is ours. Those marked *(derived)* are created by this project. A column this file cannot describe is written out as UNDOCUMENTED rather than given a plausible gloss; `--check` fails while any remain.

Source, licence, coverage and known limitations for every dataset are in `PROVENANCE.md`. Anything denominated in pounds or meals rests on the **simulated** inventory described below.

## `samples.parquet`

One row per laboratory sample. The analysis backbone.

`data/processed/samples.parquet` · Rows: 325,123 · Columns: 33

| Column | Type | Non-null | Description |
|---|---|---|---|
| `form_id` | string | 100% | The form number used to uniquely identify a specific sample. *(FSIS)* |
| `sample_number` | Int64 | 100% | The number used to uniquely identify a sample within the form_id. A single form_id can have multiple sample numbers depending on the types of tests performed. *(FSIS)* |
| `establishment_id` | Int32 | 100% | Establishment number normalised to an integer for joining to the MPI directory. FSIS recommends joining on this rather than on establishment_number, which can be reused over time. *(derived)* |
| `establishment_number` | object | 100% | Establishment mark of the real FSIS plant the simulated lot is attributed to. *(derived)* |
| `establishment_name` | object | 100% | Name of that real plant. *(derived)* |
| `establishment_state` | object | 100% | The state where the establishment is located. *(FSIS)* |
| `project_code` | object | 100% | A short name given to easily identify an FSIS sampling project. *(FSIS)* |
| `project_name` | object | 100% | The name of the FSIS sampling project. *(FSIS)* |
| `product_class` | object | 100% | Product category implied by project_code: chicken_carcass, chicken_parts, comminuted_chicken, turkey_carcass, comminuted_turkey, or an exploratory class. *(derived)* |
| `program` | object | 100% | Sampling programme implied by project_code: routine (HC_*), followup (F_*), exploratory, special, low_volume or religious_exempt. *(derived)* |
| `species` | object | 100% | chicken or turkey, from product_class. *(derived)* |
| `collection_date` | datetime64[ns] | 100% | The date the FSIS inspector collected the sample at the FSIS-regulated establishment. *(FSIS)* |
| `fy` | Int16 | 100% | Federal fiscal year of collection_date (1 October to 30 September). *(derived)* |
| `fy_file` | int64 | 100% | Fiscal-year file the record was read from. *(derived)* |
| `sample_source_name` | object | 100% | The animal or product from which the sample was obtained. *(FSIS)* |
| `product_type` | object | 52% | The specific part type collected, as entered by the inspection personnel collecting the sample (e.g., leg, quarter-carcass, livers, gizzards, hearts, and necks). This field is only applicable for the following projects:   EXP_CPT_OT01  EXP_CPT_QH01  F_CH_COM01   F_CPT_LBW01   F_TU_COM01    … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `not_analyzed` | object | 100% | Indicates if the corresponding sample was unable to be analyzed. A value of '00' indicates the sample was analyzed. *(FSIS)* |
| `sal_result` | Int8 | 100% | 1 if salmonella_sp_analysis is Positive, 0 if Negative, null otherwise. *(derived)* |
| `campy_result` | Int8 | 82% | 1/0 from the 1 mL or 30 mL Campylobacter analysis, whichever was run. *(derived)* |
| `campy_method` | string | 82% | Which Campylobacter analysis produced campy_result (1ml or 30ml). *(derived)* |
| `sal_cfu` | float64 | 3% | Numeric part of the Salmonella enumeration result. Every reported value is either '<10' or a number of 10 or more. *(derived)* |
| `sal_cfu_sign` | string | 3% | Censoring operator parsed from the enumeration string: '<' or '='. *(derived)* |
| `sal_cfu_unit` | string | 3% | ml (carcass and parts rinsate) or g (comminuted product). *(derived)* |
| `sal_cfu_ge10` | boolean | 3% | True when the sample was enumerated at 10 CFU or more, that is quantifiable rather than '<10'. Null when no count was reported. *(derived)* |
| `apc_ml` | float64 | 6% | Bacterial enumeration result (Unit: per mL): Result of the analysis to estimate the total viable aerobic bacteria count determined using the Tempo instrument. Results are reported as an estimate of the most probable number (MPN/mL) of observed positive growth responses in a standard dilution series … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `apc_ml_sign` | string | 6% | Censoring operator parsed from the aerobic plate count string ('<' or '='). *(FSIS column, described by this project)* |
| `eb_ml` | float64 | 3% | Bacterial enumeration result (Unit: per mL). Result of the analysis to estimate the total viable Enterobacteriaceae bacteria determined using the Tempo instrument. Results are reported as an estimate of the most probable number (MPN/mL) of observed positive growth responses in a standard dilution … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `eb_ml_sign` | string | 3% | Censoring operator parsed from the Enterobacteriaceae count string. *(FSIS column, described by this project)* |
| `salmonella_sp_analysis` | object | 100% | Microbiology Test: The result of the analysis for Salmonella in the sample. Negative indicates Salmonella was not found in the sample. Positive indicates Salmonella was found in the sample. *(FSIS)* |
| `salmonellae_mpn_g` | object | 1% | Microbiology Test (Unit: per gram) - Result of the analysis to estimate the population density of viable Salmonella. Results are reported as an estimate of the most probable number (MPN/g) of observed positive growth responses in a standard dilution series of sample inoculum. Salmonella MPN was … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `salmonella_mpn_qualitative` | object | 1% | Microbiology Test: Qualitative result of the analysis to estimate the population density of viable Salmonella. Salmonella most probable number (MPN) was discontinued in March 2020.   Positive = observed growth responses in at least one culture tube of a standard dilution series of the sample … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `sal_vaccine_only` | bool | 100% | True when the only Salmonella isolate for the sample is typed 'Possible Vaccine Strain'. *(derived)* |
| `sal_result_cat` | Int8 | 100% | As sal_result, but positives typed as a possible vaccine strain are set to 0. This is how FSIS counts for categorisation from 1 April 2024. *(derived)* |

## `sal_isolates.parquet`

One row per Salmonella isolate, with serotype, resistance and enumeration detail.

`data/processed/sal_isolates.parquet` · Rows: 37,695 · Columns: 96

| Column | Type | Non-null | Description |
|---|---|---|---|
| `form_id` | string | 100% | The form number used to uniquely identify a specific sample. *(FSIS)* |
| `fsis_number` | object | 81% | The FSIS number is a unique identifier for retrieving whole genome sequence data from the National Center for Biotechnology and Information (NCBI) Pathogen Detection Isolates Browser (https://www.ncbi.nlm.nih.gov/pathogens/isolates/). NCBI developed the Browser to help users learn about the … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `pathogen_number` | object | 100% | A combination of the pathogen and the primary sample number. The primary sample number is known as the 'sample_number' in the primary dataset. The pathogen is indicated by a four-letter code:   SALM: Salmonella   O157: E. coli O157:H7   ECOL: Generic E. coli   STEC: Shiga toxin-producing E. coli of … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `fy_file` | int64 | 100% | Fiscal-year file the record was read from. *(derived)* |
| `allele_code_version` | object | 61% | The first part of the composite allele code assigned by CDC-PulseNet (https://www.cdc.gov/pulsenet/index.html). The version is comprised of the organism and the naming script used. When PulseNet is unable to assign an allele code, the entry will be: Allele Code Ineligible. *(FSIS)* |
| `allele_code` | object | 61% | A code assigned by CDC-PulseNet (https://www.cdc.gov/pulsenet/index.html) based on the number of differences in pre-defined genes in the WGS data. When PulseNet is unable to assign an allele code, the entry will be: Allele Code Ineligible. *(FSIS)* |
| `allele_code_date` | object | 61% | The date when FSIS retrieved the salmonella_allele_code from CDC-PulseNet (https://www.cdc.gov/pulsenet/index.html). *(FSIS)* |
| `sra_accession_number` | object | 81% | A unique identifier for retrieving raw sequencing data and alignment information from the Sequence Read Archive (SRA) from the National Center for Biotechnology and Information (NCBI) database. *(FSIS)* |
| `bio_sample_accession_number` | object | 81% | A unique identifier that links to isolate metadata. Data users can use the accession number to search for isolates with the NCBI Isolate Browser from the National Institute of Health (NIH). *(FSIS)* |
| `bio_project_number` | object | 81% | A unique identifier for retrieving biological source materials data from the BioProject database from the National Center for Biotechnology and Information (NCBI) database. *(FSIS)* |
| `multi_locus_sequence` | object | 49% | Subtyping scheme based on 7 housekeeping genes used to group isolates at a broad level (more discriminatory than species but not necessarily serotype). *(FSIS)* |
| `resistance_genotype` | object | 62% | Antimicrobial resistance genes identified in the Salmonella isolate by NCBI using AMRFinderPlus tool (https://www.ncbi.nlm.nih.gov/pathogens/antimicrobial-resistance/AMRFinder/). NCBI's AMRFinderPlus tool relies on NCBI's curated Reference Gene Database … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `stress_genotype` | object | 62% | Stress resistance genes identified in the Salmonella isolate by NCBI using AMRFinderPlus tool (https://www.ncbi.nlm.nih.gov/pathogens/antimicrobial-resistance/AMRFinder/). NCBI's AMRFinderPlus tool relies on NCBI's curated Reference Gene Database (https://www.ncbi.nlm.nih.gov/pathogens/refgene/#). *(FSIS)* |
| `virulence_genotype` | object | 59% | Virulence resistance genes identified in the Salmonella isolate by NCBI using AMRFinderPlus tool (https://www.ncbi.nlm.nih.gov/pathogens/antimicrobial-resistance/AMRFinder/). NCBI's AMRFinderPlus tool relies on NCBI's curated Reference Gene Database … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `serotype` | object | 100% | Follow-up Microbiology Test - Salmonella Serotype. The name of the distinct variation of the tested species of bacteria. A list of the serotypes that are more commonly associated with human illness can be found on the Centers for Disease Control and Prevention (CDC) web site on their National … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `primary_pfge_pattern` | object | 39% | The specific primary pattern identified from Pulsed-Field Gel Electrophoresis (PFGE), which is the laboratory technique used to produce a deoxyribonucleic acid (DNA) fingerprint for a group of the same type of bacteria. FSIS discontinued PFGE characterization in March 2019 and replaced the … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `secondary_pfge_pattern` | object | 39% | The specific secondary pattern identified from Pulsed-Field Gel Electrophoresis (PFGE), which is the laboratory technique used to produce a deoxyribonucleic acid (DNA) fingerprint for a group of the same type of bacteria. FSIS discontinued PFGE characterization in March 2019 and replaced the … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ampicillin_operator` | object | 74% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ampicillin_mic` | float64 | 74% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ampicillin_resistant_ast` | boolean | 74% | Yes - The salmonella isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The salmonella isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `amoxicillin_clavulanic_acid_operator` | object | 74% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `amoxicillin_clavulanic_acid_mic` | float64 | 74% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `amoxicillin_clavulanic_acid_resistant_ast` | boolean | 74% | Yes - The salmonella isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The salmonella isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ceftriaxone_operator` | object | 74% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ceftriaxone_mic` | float64 | 74% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ceftriaxone_resistant_ast` | boolean | 74% | Yes - The salmonella isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The salmonella isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `azithromycin_operator` | object | 74% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `azithromycin_mic` | float64 | 74% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `azithromycin_resistant_ast` | boolean | 74% | Yes - The salmonella isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The salmonella isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `chloramphenicol_operator` | object | 74% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `chloramphenicol_mic` | float64 | 74% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `chloramphenicol_resistant_ast` | boolean | 74% | Yes - The salmonella isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The salmonella isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ciprofloxacin_operator` | object | 74% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ciprofloxacin_mic` | float64 | 74% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ciprofloxacin_resistant_ast` | boolean | 74% | Yes - The salmonella isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The salmonella isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `colistin_operator` | object | 28% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `colistin_mic` | float64 | 28% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `colistin_resistant_ast` | boolean | 28% | Yes - The salmonella isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The salmonella isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `trimethoprim_sulfamethoxazole_operator` | object | 74% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `trimethoprim_sulfamethoxazole_mic` | float64 | 74% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `trimethoprim_sulfamethoxazole_resistant_ast` | boolean | 74% | Yes - The salmonella isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The salmonella isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `cefoxitin_operator` | object | 74% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `cefoxitin_mic` | float64 | 74% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `cefoxitin_resistant_ast` | boolean | 74% | Yes - The salmonella isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The salmonella isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `gentamicin_operator` | object | 74% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `gentamicin_mic` | float64 | 74% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `gentamicin_resistant_ast` | boolean | 74% | Yes - The salmonella isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The salmonella isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `kanamycin_operator` | object | 2% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `kanamycin_mic` | float64 | 2% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `kanamycin_resistant_ast` | boolean | 2% | Yes - The salmonella isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The salmonella isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `meropenem_operator` | object | 60% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `meropenem_mic` | float64 | 60% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `meropenem_resistant_ast` | boolean | 60% | Yes - The salmonella isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The salmonella isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `nalidixic_acid_operator` | object | 74% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `nalidixic_acid_mic` | float64 | 74% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `nalidixic_acid_resistant_ast` | boolean | 74% | Yes - The salmonella isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The salmonella isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `sulfisoxazole_operator` | object | 74% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `sulfisoxazole_mic` | float64 | 74% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `sulfisoxazole_resistant_ast` | boolean | 74% | Yes - The salmonella isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The salmonella isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `streptomycin_operator` | object | 46% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `streptomycin_mic` | float64 | 46% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `streptomycin_resistant_ast` | boolean | 46% | Yes - The salmonella isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The salmonella isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `tetracycline_operator` | object | 74% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `tetracycline_mic` | float64 | 74% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `tetracycline_resistant_ast` | boolean | 74% | Yes - The salmonella isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The salmonella isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ceftiofur_operator` | object | 15% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ceftiofur_mic` | float64 | 15% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ceftiofur_resistant_ast` | boolean | 15% | Yes - The salmonella isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The salmonella isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ampicillin_resistant_wgs` | boolean | 19% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `amoxicillin_clavulanic_acid_resistant_wgs` | boolean | 19% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ceftriaxone_resistant_wgs` | boolean | 19% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `azithromycin_resistant_wgs` | boolean | 19% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `chloramphenicol_resistant_wgs` | boolean | 19% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ciprofloxacin_resistant_wgs` | boolean | 19% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `colistin_resistant_wgs` | boolean | 19% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `trimethoprim_sulfamethoxazole_resistant_wgs` | boolean | 19% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `cefoxitin_resistant_wgs` | boolean | 19% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `gentamicin_resistant_wgs` | boolean | 19% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `kanamycin_resistant_wgs` | boolean | 19% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `meropenem_resistant_wgs` | boolean | 19% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `nalidixic_acid_resistant_wgs` | boolean | 19% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `sulfisoxazole_resistant_wgs` | boolean | 19% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `streptomycin_resistant_wgs` | boolean | 19% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `tetracycline_resistant_wgs` | boolean | 19% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ceftiofur_resistant_wgs` | boolean | 19% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `sequenced` | bool | 100% | True when the isolate has an SRA accession, that is it was whole-genome sequenced. *(FSIS column, described by this project)* |
| `serotype_clean` | object | 100% | Serotype string normalised for grouping: whitespace and case regularised, FSIS's vaccine-strain annotation preserved as a distinct value rather than folded into Typhimurium. *(derived)* |
| `vaccine_strain` | boolean | 100% | True when FSIS typed the isolate as a possible vaccine strain. From 1 April 2024 FSIS excludes these when categorising establishments, and so does this project. *(FSIS column, described by this project)* |
| `establishment_id` | Int32 | 100% | Establishment number normalised to an integer for joining to the MPI directory. FSIS recommends joining on this rather than on establishment_number, which can be reused over time. *(derived)* |
| `establishment_state` | object | 100% | The state where the establishment is located. *(FSIS)* |
| `collection_date` | datetime64[ns] | 100% | The date the FSIS inspector collected the sample at the FSIS-regulated establishment. *(FSIS)* |
| `fy` | Int16 | 100% | Federal fiscal year of collection_date (1 October to 30 September). *(derived)* |
| `project_code` | object | 100% | A short name given to easily identify an FSIS sampling project. *(FSIS)* |
| `product_class` | object | 100% | Product category implied by project_code: chicken_carcass, chicken_parts, comminuted_chicken, turkey_carcass, comminuted_turkey, or an exploratory class. *(derived)* |
| `program` | object | 100% | Sampling programme implied by project_code: routine (HC_*), followup (F_*), exploratory, special, low_volume or religious_exempt. *(derived)* |
| `species` | object | 100% | chicken or turkey, from product_class. *(derived)* |

## `campy_isolates.parquet`

One row per Campylobacter isolate.

`data/processed/campy_isolates.parquet` · Rows: 35,662 · Columns: 68

| Column | Type | Non-null | Description |
|---|---|---|---|
| `form_id` | string | 100% | The form number used to uniquely identify a specific sample. *(FSIS)* |
| `fsis_number` | object | 94% | The FSIS number is a unique identifier for retrieving whole genome sequence data from the National Center for Biotechnology and Information (NCBI) Pathogen Detection Isolates Browser (https://www.ncbi.nlm.nih.gov/pathogens/isolates/). NCBI developed the Browser to help users learn about the … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `pathogen_number` | object | 100% | A combination of the pathogen and the primary sample number. The primary sample number is known as the 'sample_number' in the primary dataset. The pathogen is indicated by a four-letter code:   SALM: Salmonella   O157: E. coli O157:H7   ECOL: Generic E. coli   STEC: Shiga toxin-producing E. coli of … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `fy_file` | int64 | 100% | Fiscal-year file the record was read from. *(derived)* |
| `allele_code_version` | object | 70% | The first part of the composite allele code assigned by CDC-PulseNet (https://www.cdc.gov/pulsenet/index.html). The version is comprised of the organism and the naming script used. When PulseNet is unable to assign an allele code, the entry will be: Allele Code Ineligible. *(FSIS)* |
| `allele_code` | object | 67% | A code generated using CDC PulseNet allele calls based on the number of differences in pre-defined genes in the WGS data. When PulseNet is unable to assign an allele code, the entry will be: Allele Code Ineligible. *(FSIS)* |
| `allele_code_date` | object | 70% | The date when FSIS generated the campylobacter_allele_code using CDC PulseNet allele calls. *(FSIS)* |
| `sra_accession_number` | object | 94% | A unique identifier for retrieving raw sequencing data and alignment information from the Sequence Read Archive (SRA) from the National Center for Biotechnology and Information (NCBI) database. *(FSIS)* |
| `bio_sample_accession_number` | object | 94% | A unique identifier that links to isolate metadata. Data users can use the accession number to search for isolates with the NCBI Isolate Browser from the National Institute of Health (NIH). *(FSIS)* |
| `bio_project_number` | object | 94% | A unique identifier for retrieving biological source materials data from the BioProject database from the National Center for Biotechnology and Information (NCBI) database. *(FSIS)* |
| `multi_locus_sequence` | object | 0% | Subtyping scheme based on 7 housekeeping genes used to group isolates at a broad level (more discriminatory than species but not necessarily serotype). *(FSIS)* |
| `resistance_genotype` | object | 62% | Antimicrobial resistance genes identified in the Campylobacter isolate by NCBI using AMRFinderPlus tool (https://www.ncbi.nlm.nih.gov/pathogens/antimicrobial-resistance/AMRFinder/). NCBI's AMRFinderPlus tool relies on NCBI's curated Reference Gene Database … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `stress_genotype` | object | 48% | Stress resistance genes identified in the Campylobacter isolate by NCBI using AMRFinderPlus tool (https://www.ncbi.nlm.nih.gov/pathogens/antimicrobial-resistance/AMRFinder/). NCBI's AMRFinderPlus tool relies on NCBI's curated Reference Gene Database … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `virulence_genotype` | object | 0% | Virulence resistance genes identified in the Campylobacter isolate by NCBI using AMRFinderPlus tool (https://www.ncbi.nlm.nih.gov/pathogens/antimicrobial-resistance/AMRFinder/). NCBI's AMRFinderPlus tool relies on NCBI's curated Reference Gene Database … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `jejuni` | object | 100% | Species designation for isolates belonging to the genus Campylobacter. If positive, the species is determined to be jejuni. *(FSIS)* |
| `coli` | object | 100% | Species designation for isolates belonging to the genus Campylobacter. If positive, the species is determined to be coli. *(FSIS)* |
| `lari` | object | 100% | Species designation for isolates belonging to the genus Campylobacter. If positive, the species is determined to be lari. *(FSIS)* |
| `primary_pfge_pattern` | object | 14% | The specific primary pattern identified from Pulsed-Field Gel Electrophoresis (PFGE), which is the laboratory technique used to produce a deoxyribonucleic acid (DNA) fingerprint for a group of the same type of bacteria. FSIS discontinued PFGE characterization in March 2019 and replaced the … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `secondary_pfge_pattern` | object | 14% | The specific secondary pattern identified from Pulsed-Field Gel Electrophoresis (PFGE), which is the laboratory technique used to produce a deoxyribonucleic acid (DNA) fingerprint for a group of the same type of bacteria. FSIS discontinued PFGE characterization in March 2019 and replaced the … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `azithromycin_operator` | object | 79% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `azithromycin_mic` | float64 | 79% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `azithromycin_resistant_ast` | boolean | 79% | Yes - The campylobacter isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The campylobacter isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ciprofloxacin_operator` | object | 79% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ciprofloxacin_mic` | float64 | 79% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ciprofloxacin_resistant_ast` | boolean | 79% | Yes - The campylobacter isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The campylobacter isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `clindamycin_operator` | object | 79% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `clindamycin_mic` | float64 | 79% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `clindamycin_resistant_ast` | boolean | 79% | Yes - The campylobacter isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The campylobacter isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `erythromycin_operator` | object | 79% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `erythromycin_mic` | float64 | 79% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `erythromycin_resistant_ast` | boolean | 79% | Yes - The campylobacter isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The campylobacter isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `florfenicol_operator` | object | 79% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `florfenicol_mic` | float64 | 79% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `florfenicol_resistant_ast` | boolean | 79% | Yes - The campylobacter isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The campylobacter isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `gentamicin_operator` | object | 79% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `gentamicin_mic` | float64 | 79% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `gentamicin_resistant_ast` | boolean | 79% | Yes - The campylobacter isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The campylobacter isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `meropenem_operator` | object | 51% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `meropenem_mic` | float64 | 51% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `meropenem_resistant_ast` | boolean | 51% | Yes - The campylobacter isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The campylobacter isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `nalidixic_acid_operator` | object | 79% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `nalidixic_acid_mic` | float64 | 79% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `nalidixic_acid_resistant_ast` | boolean | 79% | Yes - The campylobacter isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The campylobacter isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `telithromycin_operator` | object | 17% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `telithromycin_mic` | float64 | 17% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `telithromycin_resistant_ast` | boolean | 17% | Yes - The campylobacter isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The campylobacter isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `tetracycline_operator` | object | 79% | Indicates if the actual resistance point of the given pathogen to the given antimicrobial is greater than, less than, or equal to the accompanying Minimum Inhibitory Concentration (MIC) value. For example, if the MIC value is 256 and the operator is  >, then the organism was resistant to a … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `tetracycline_mic` | float64 | 79% | The minimum tested concentration (μg/ml) of the antimicrobial drug found to completely inhibit growth of the isolate. If the MIC value recorded is the lowest concentration in the testing range, the MIC value is determined to be equal to or less than the tested concentration. If the MIC value … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `tetracycline_resistant_ast` | boolean | 79% | Yes - The campylobacter isolate's MIC value for the antimicrobial drug meets the resistant breakpoint criteria and is considered resistant based on AST.     No - The campylobacter isolate's MIC value for the antimicrobial drug does not meet the resistant breakpoint criteria and is not considered … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `azithromycin_resistant_wgs` | boolean | 22% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `ciprofloxacin_resistant_wgs` | boolean | 22% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `clindamycin_resistant_wgs` | boolean | 22% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `erythromycin_resistant_wgs` | boolean | 22% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `florfenicol_resistant_wgs` | boolean | 22% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `gentamicin_resistant_wgs` | boolean | 22% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `meropenem_resistant_wgs` | boolean | 22% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `nalidixic_acid_resistant_wgs` | boolean | 22% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `telithromycin_resistant_wgs` | boolean | 22% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `tetracycline_resistant_wgs` | boolean | 22% | FSIS is transitioning from antimicrobial susceptibility testing (AST) in determining antimicrobial resistance (AMR) to predicting AMR using whole genome sequencing (WGS).   Yes - The pathogen's WGS profile predicts that the isolate is resistant to the antimicrobial.    No - The pathogen's WGS … *(full text in `data_dictionary_primary.csv` / `data_dictionary_secondary.csv`)* *(FSIS)* |
| `sequenced` | bool | 100% | True when the isolate has an SRA accession, that is it was whole-genome sequenced. *(FSIS column, described by this project)* |
| `establishment_id` | Int32 | 100% | Establishment number normalised to an integer for joining to the MPI directory. FSIS recommends joining on this rather than on establishment_number, which can be reused over time. *(derived)* |
| `establishment_state` | object | 100% | The state where the establishment is located. *(FSIS)* |
| `collection_date` | datetime64[ns] | 100% | The date the FSIS inspector collected the sample at the FSIS-regulated establishment. *(FSIS)* |
| `fy` | Int16 | 100% | Federal fiscal year of collection_date (1 October to 30 September). *(derived)* |
| `project_code` | object | 100% | A short name given to easily identify an FSIS sampling project. *(FSIS)* |
| `product_class` | object | 100% | Product category implied by project_code: chicken_carcass, chicken_parts, comminuted_chicken, turkey_carcass, comminuted_turkey, or an exploratory class. *(derived)* |
| `program` | object | 100% | Sampling programme implied by project_code: routine (HC_*), followup (F_*), exploratory, special, low_volume or religious_exempt. *(derived)* |
| `species` | object | 100% | chicken or turkey, from product_class. *(derived)* |

## `cecal.parquet`

NARMS cecal sampling at slaughter.

`data/processed/cecal.parquet` · Rows: 72,151 · Columns: 29

| Column | Type | Non-null | Description |
|---|---|---|---|
| `establishment_id` | Int32 | 100% | Establishment number normalised to an integer for joining to the MPI directory. FSIS recommends joining on this rather than on establishment_number, which can be reused over time. *(derived)* |
| `establishment_number` | object | 100% | Establishment mark of the real FSIS plant the simulated lot is attributed to. *(derived)* |
| `establishment_name` | object | 100% | Name of that real plant. *(derived)* |
| `establishment_state` | object | 100% | The state where the establishment is located. *(FSIS)* |
| `project_code` | object | 100% | A short name given to easily identify an FSIS sampling project. *(FSIS)* |
| `project_name` | object | 100% | The name of the FSIS sampling project. *(FSIS)* |
| `slaughter_class` | object | 100% | Animal class sampled, as FSIS writes it, for example 'Animal-Cattle-Heifer' or 'Animal-Swine-Market Swine'. The cecal programme covers cattle and swine as well as poultry; poultry analysis filters on this. *(FSIS column, described by this project)* |
| `form_id` | string | 100% | The form number used to uniquely identify a specific sample. *(FSIS)* |
| `collection_date` | datetime64[ns] | 100% | The date the FSIS inspector collected the sample at the FSIS-regulated establishment. *(FSIS)* |
| `salmonella_sp` | object | 95% | FSIS's Salmonella result for the cecal sample, as published: Positive or Negative. *(FSIS column, described by this project)* |
| `salmonella_molecular_serotype` | object | 23% | Serotype FSIS assigned to the cecal Salmonella isolate from sequence data. *(FSIS column, described by this project)* |
| `salmonella_fsis_number` | object | 20% | FSIS's internal identifier for the cecal Salmonella isolate. *(FSIS column, described by this project)* |
| `salmonella_sra_accession_number` | object | 20% | A unique identifier for retrieving raw sequencing data and alignment information from the Sequence Read Archive (SRA) from the National Center for Biotechnology and Information (NCBI) database. *(FSIS)* |
| `campylobacter` | object | 77% | FSIS's Campylobacter result for the cecal sample: Positive or Negative. *(FSIS column, described by this project)* |
| `campylobacter_coli` | object | 27% | Species designation for isolates belonging to the genus Campylobacter. If positive, the species is determined to be coli. *(FSIS)* |
| `campylobacter_jejuni` | object | 27% | Species designation for isolates belonging to the genus Campylobacter. If positive, the species is determined to be jejuni. *(FSIS)* |
| `campylobacter_lari` | object | 27% | Species designation for isolates belonging to the genus Campylobacter. If positive, the species is determined to be lari. *(FSIS)* |
| `campylobacter_sra_accession_number` | object | 22% | A unique identifier for retrieving raw sequencing data and alignment information from the Sequence Read Archive (SRA) from the National Center for Biotechnology and Information (NCBI) database. *(FSIS)* |
| `e_coli` | object | 32% | FSIS's generic E. coli result for the cecal sample: Positive or Negative. Generic E. coli is an indicator organism here, not a pathogen finding. *(FSIS column, described by this project)* |
| `e_coli_sra_accession_number` | object | 13% | SRA accession for the cecal E. coli isolate, where sequenced. *(FSIS column, described by this project)* |
| `enterococcus` | object | 32% | FSIS's Enterococcus result for the cecal sample: Positive or Negative. Carried as an antimicrobial-resistance indicator organism. *(FSIS column, described by this project)* |
| `enterococcus_species` | object | 13% | Enterococcus species identified, for example faecalis, faecium, gallinarum. *(FSIS column, described by this project)* |
| `enterococcus_sra_accession_number` | object | 7% | SRA accession for the cecal Enterococcus isolate, where sequenced. *(FSIS column, described by this project)* |
| `fy_file` | int64 | 100% | Fiscal-year file the record was read from. *(derived)* |
| `fy` | Int16 | 100% | Federal fiscal year of collection_date (1 October to 30 September). *(derived)* |
| `salmonella_sp_result` | Int8 | 95% | 1/0 recoding of salmonella_sp for arithmetic. *(derived)* |
| `campylobacter_result` | Int8 | 77% | 1/0 recoding of campylobacter. *(derived)* |
| `e_coli_result` | Int8 | 32% | 1/0 recoding of e_coli. *(derived)* |
| `enterococcus_result` | Int8 | 32% | 1/0 recoding of enterococcus. *(derived)* |

## `establishments.parquet`

MPI directory and demographic data, active and inactive.

`data/processed/establishments.parquet` · Rows: 8,188 · Columns: 42

| Column | Type | Non-null | Description |
|---|---|---|---|
| `establishment_id` | Int32 | 100% | Establishment number normalised to an integer for joining to the MPI directory. FSIS recommends joining on this rather than on establishment_number, which can be reused over time. *(derived)* |
| `establishment_number` | object | 100% | Establishment mark of the real FSIS plant the simulated lot is attributed to. *(derived)* |
| `establishment_name` | object | 100% | Name of that real plant. *(derived)* |
| `duns_number` | object | 15% | Dun & Bradstreet number for the company, as listed in the MPI directory. *(FSIS column, described by this project)* |
| `city` | object | 100% | City of the establishment. *(FSIS column, described by this project)* |
| `state` | object | 100% | Two-letter US state code. *(derived)* |
| `zip` | object | 100% | Postal code of the establishment. *(FSIS column, described by this project)* |
| `grant_date` | datetime64[ns] | 100% | Date FSIS granted inspection. For inactive establishments this is the earliest grant date. *(FSIS column, described by this project)* |
| `activities` | object | 91% | Semicolon-separated list of inspected activities at the establishment, for example 'Meat Processing; Poultry Slaughter'. *(FSIS column, described by this project)* |
| `dbas` | object | 31% | Semicolon-separated 'doing business as' names. *(FSIS column, described by this project)* |
| `district` | object | 100% | FSIS district office code. *(FSIS column, described by this project)* |
| `circuit` | object | 100% | FSIS inspection circuit code within the district. *(FSIS column, described by this project)* |
| `size` | object | 98% | FSIS HACCP size category: Large, Small, Very Small, or 'N / A' where not assigned. *(FSIS column, described by this project)* |
| `latitude` | float64 | 100% | Station latitude. *(derived)* |
| `longitude` | float64 | 100% | Station longitude. *(derived)* |
| `county` | object | 100% | County name as SVI spells it. *(derived)* |
| `fips_code` | object | 99% | Five-digit county FIPS code of the establishment, used to join county vulnerability. *(FSIS column, described by this project)* |
| `active` | bool | 100% | True for establishments from the active MPI directory, False for those from the inactive directory. *(derived)* |
| `inactive_effective_date` | datetime64[ns] | 12% | Date the grant of inspection ceased, for inactive establishments. *(FSIS column, described by this project)* |
| `active_poultry_grant` | boolean | 100% | True when the establishment holds a current poultry grant of inspection. *(FSIS column, described by this project)* |
| `inspection_system_npis` | boolean | 100% | True when the establishment operates under the New Poultry Inspection System. *(FSIS column, described by this project)* |
| `inspection_system_npis_waiver` | boolean | 100% | True when the establishment holds a waiver related to NPIS. *(FSIS column, described by this project)* |
| `poultry_exemption_religious` | boolean | 100% | True when the establishment operates under the religious-exemption provision for poultry slaughter. *(FSIS column, described by this project)* |
| `slaughter` | boolean | 100% | True when the establishment slaughters. *(FSIS column, described by this project)* |
| `processing` | boolean | 100% | True when the establishment processes. *(FSIS column, described by this project)* |
| `processing_volume_category` | float64 | 72% | FSIS processing volume band, 1 to 5, larger is higher volume. Published as a band rather than a volume. *(FSIS column, described by this project)* |
| `slaughter_volume_category` | float64 | 17% | FSIS slaughter volume band, 1 to 5, larger is higher volume. *(FSIS column, described by this project)* |
| `young_chicken_slaughter` | boolean | 100% | True when the establishment slaughters young chickens. *(FSIS column, described by this project)* |
| `young_turkey_slaughter` | boolean | 100% | True when the establishment slaughters young turkeys. *(FSIS column, described by this project)* |
| `raw_intact_poultry_processing` | boolean | 100% | True when the establishment processes raw intact poultry. *(FSIS column, described by this project)* |
| `raw_non_intact_poultry_processing` | boolean | 100% | True when the establishment processes raw non-intact poultry, which includes comminuted product. *(FSIS column, described by this project)* |
| `rte_poultry_processing` | boolean | 100% | True when the establishment produces ready-to-eat poultry. *(FSIS column, described by this project)* |
| `nrte_poultry_processing` | boolean | 100% | True when the establishment produces not-ready-to-eat poultry. *(FSIS column, described by this project)* |
| `category_start_date` | datetime64[ns] | 9% | First day of the 52-week window the posted Salmonella categories cover. *(FSIS column, described by this project)* |
| `category_end_date` | datetime64[ns] | 9% | Last day of that window. *(FSIS column, described by this project)* |
| `young_chicken_carcasses_category` | object | 2% | Salmonella Category 1, 2 or 3 FSIS posted for young chicken carcasses at this establishment. *(FSIS column, described by this project)* |
| `young_turkey_carcasses_category` | object | 0% | Posted Salmonella category for young turkey carcasses. *(FSIS column, described by this project)* |
| `comminuted_chicken_category` | object | 0% | Posted Salmonella category for comminuted chicken. *(FSIS column, described by this project)* |
| `comminuted_turkey_category` | object | 0% | Posted Salmonella category for comminuted turkey. *(FSIS column, described by this project)* |
| `chicken_parts_category` | object | 5% | Posted Salmonella category for chicken parts. *(FSIS column, described by this project)* |
| `haccp_size` | object | 88% | FSIS HACCP size category of that plant (Large, Small, Very Small). *(derived)* |
| `company_key` | object | 100% | First two words of the establishment name, upper-cased and stripped of punctuation. A coarse company grouping used only to spot the same firm across several plants; it is not an FSIS identifier and will both split and merge companies. *(derived)* |

## `posted_categories.parquet`

Categories FSIS actually published, used to validate the rebuild.

`data/processed/posted_categories.parquet` · Rows: 1,089 · Columns: 9

| Column | Type | Non-null | Description |
|---|---|---|---|
| `establishment_number` | object | 100% | Establishment mark of the real FSIS plant the simulated lot is attributed to. *(derived)* |
| `establishment_name` | object | 100% | Name of that real plant. *(derived)* |
| `city` | object | 100% | City of the establishment. *(FSIS column, described by this project)* |
| `state` | object | 100% | Two-letter US state code. *(derived)* |
| `district` | object | 100% | FSIS district office code. *(FSIS column, described by this project)* |
| `product_class_posted` | object | 100% | Product class exactly as the FSIS posting labels it, before mapping to this project's product_class. *(derived)* |
| `category` | object | 100% | FSIS Salmonella Category 1, 2, 3 or NA, rebuilt from raw samples on the 52-week moving window by fsis_categories.py. Validated against three official postings at 99.75% agreement over 2,764 rows. *(derived)* |
| `window_text` | object | 100% | The sample-collection period as printed in the posting, kept verbatim so the window can be audited against the source. *(derived)* |
| `source_file` | object | 100% | Which posted-category workbook the row came from. *(derived)* |

## `posted_aggregate.parquet`

FSIS's own aggregate category counts.

`data/processed/posted_aggregate.parquet` · Rows: 60 · Columns: 7

| Column | Type | Non-null | Description |
|---|---|---|---|
| `product_class_posted` | object | 100% | Product class exactly as the FSIS posting labels it, before mapping to this project's product_class. *(derived)* |
| `category` | object | 100% | FSIS Salmonella Category 1, 2, 3 or NA, rebuilt from raw samples on the 52-week moving window by fsis_categories.py. Validated against three official postings at 99.75% agreement over 2,764 rows. *(derived)* |
| `haccp_size` | object | 100% | FSIS HACCP size category of that plant (Large, Small, Very Small). *(derived)* |
| `establishments` | int64 | 100% | Number of establishments FSIS reports in that category and product class. *(FSIS column, described by this project)* |
| `percent` | float64 | 100% | Percentage of rated establishments FSIS reports in that category and product class. *(FSIS column, described by this project)* |
| `window_text` | object | 100% | The sample-collection period as printed in the posting, kept verbatim so the window can be audited against the source. *(derived)* |
| `source_file` | object | 100% | Which posted-category workbook the row came from. *(derived)* |

## `nors_poultry_serotype_year.csv`

CDC NORS outbreak burden by IFSAC poultry category, serotype and year. Joined to FSIS at serotype and year only.

`data/nors/nors_poultry_serotype_year.csv` · Rows: 96 · Columns: 7

| Column | Type | Non-null | Description |
|---|---|---|---|
| `year` | int64 | 100% | Calendar year. *(derived)* |
| `cat` | object | 100% | IFSAC food category the outbreak was attributed to, from NORS field ifsac_category. The join to FSIS is made on this and on year, never on an establishment. *(derived)* |
| `sero` | object | 96% | Serotype or genotype as NORS records it (field serotype_or_genotype). Not harmonised with FSIS serotype spelling; matched case-insensitively on the leading token. *(derived)* |
| `nb` | int64 | 100% | Number of outbreaks in the group. *(derived)* |
| `ill` | int64 | 100% | Sum of reported illnesses across those outbreaks. *(derived)* |
| `hosp` | int64 | 100% | Sum of reported hospitalisations. Sparse: a single large outbreak can dominate a serotype-year, and 10b flags any share above 80% as resting on one event. *(derived)* |
| `dth` | int64 | 100% | Sum of reported deaths. *(derived)* |

## `nors_salmonella_attribution.csv`

CDC NORS Salmonella burden by food category, all foods.

`data/nors/nors_salmonella_attribution.csv` · Rows: 25 · Columns: 5

| Column | Type | Non-null | Description |
|---|---|---|---|
| `cat` | object | 92% | IFSAC food category the outbreak was attributed to, from NORS field ifsac_category. The join to FSIS is made on this and on year, never on an establishment. *(derived)* |
| `nb` | int64 | 100% | Number of outbreaks in the group. *(derived)* |
| `ill` | int64 | 100% | Sum of reported illnesses across those outbreaks. *(derived)* |
| `hosp` | int64 | 100% | Sum of reported hospitalisations. Sparse: a single large outbreak can dominate a serotype-year, and 10b flags any share above 80% as resting on one event. *(derived)* |
| `dth` | int64 | 100% | Sum of reported deaths. *(derived)* |

## `noaa_state_month.csv`

NOAA GSOM monthly climate, averaged over a fixed station panel per state.

`data/noaa/noaa_state_month.csv` · Rows: 7,644 · Columns: 8

| Column | Type | Non-null | Description |
|---|---|---|---|
| `state` | object | 100% | Two-letter US state code. *(derived)* |
| `date` | object | 100% | Month the observation covers, as the first day of that month. *(derived)* |
| `PRCP` | float64 | 100% | Mean monthly precipitation across the state's station panel, in millimetres. NOAA CDO was queried with units=metric. *(derived)* |
| `TAVG` | float64 | 100% | Mean monthly average temperature across the station panel, in degrees Celsius. *(derived)* |
| `TMAX` | float64 | 100% | Mean monthly maximum temperature across the station panel, in degrees Celsius. *(derived)* |
| `n_stations` | int64 | 100% | Stations contributing to that state-month. Fewer stations means a noisier mean, so this is kept rather than hidden. *(derived)* |
| `year` | int64 | 100% | Calendar year. *(derived)* |
| `month` | int64 | 100% | Calendar month, 1 to 12. *(derived)* |

## `noaa_stations_used.csv`

The station panel itself, so the climate series is reproducible.

`data/noaa/noaa_stations_used.csv` · Rows: 332 · Columns: 8

| Column | Type | Non-null | Description |
|---|---|---|---|
| `state` | object | 100% | Two-letter US state code. *(derived)* |
| `station` | object | 100% | NOAA station identifier. *(derived)* |
| `name` | object | 100% | NOAA station name. *(derived)* |
| `datacoverage` | float64 | 100% | NOAA's own completeness fraction for the station over the requested window. Stations are chosen deterministically by this descending, then by id, so the panel is reproducible. *(derived)* |
| `mindate` | object | 100% | First date NOAA holds for the station. *(derived)* |
| `maxdate` | object | 100% | Last date NOAA holds for the station. *(derived)* |
| `latitude` | float64 | 100% | Station latitude. *(derived)* |
| `longitude` | float64 | 100% | Station longitude. *(derived)* |

## `fsis_recalls_poultry_salmonella.csv`

FSIS recalls and public health alerts filtered to poultry or Salmonella.

`data/fsis_recalls/fsis_recalls_poultry_salmonella.csv` · Rows: 563 · Columns: 17

| Column | Type | Non-null | Description |
|---|---|---|---|
| `recall_number` | object | 100% | FSIS recall case number. *(derived)* |
| `recall_date` | object | 100% | Date FSIS published the recall or public health alert. *(derived)* |
| `year` | int64 | 100% | Calendar year. *(derived)* |
| `risk_level` | object | 100% | FSIS risk level for the recall. *(derived)* |
| `recall_class` | object | 100% | FSIS recall classification (I, II, III). *(derived)* |
| `recall_type` | object | 100% | Whether the notice is a recall or a public health alert. *(derived)* |
| `reason` | object | 98% | FSIS's stated reason for the recall. *(derived)* |
| `outbreak_related` | object | 77% | FSIS's own flag that the recall is outbreak-associated. Carried through as published; this project draws no causal link of its own between any establishment and any illness. *(derived)* |
| `active_notice` | object | 91% | Whether FSIS still lists the notice as active. *(derived)* |
| `company` | object | 66% | Recalling company as FSIS names it. *(derived)* |
| `est_marks` | object | 37% | Establishment marks recovered from the notice text by regular expression. Recoverable for only 206 of 563 poultry-or-Salmonella notices (36.6%), so an establishment with no linked recall may simply be unresolvable rather than clean. *(derived)* |
| `n_states` | int64 | 100% | Number of states in the distribution list. *(derived)* |
| `states` | object | 67% | Distribution states as listed. *(derived)* |
| `is_poultry_title` | bool | 100% | True when the notice title matches this project's poultry filter. *(derived)* |
| `is_salmonella` | bool | 100% | True when the notice mentions Salmonella. *(derived)* |
| `title` | object | 100% | Notice title as published. *(derived)* |
| `url` | object | 100% | Link to the notice on fsis.usda.gov. *(derived)* |

## `vulnerability_county.csv`

CDC/ATSDR SVI 2022 by county, plus Census ACS where the key was accepted.

`data/vulnerability/vulnerability_county.csv` · Rows: 3,144 · Columns: 10

| Column | Type | Non-null | Description |
|---|---|---|---|
| `fips` | int64 | 100% | Five-digit county FIPS code, zero-padded. *(derived)* |
| `state_name` | object | 100% | State name as SVI spells it. *(derived)* |
| `state` | object | 100% | Two-letter US state code. *(derived)* |
| `county` | object | 100% | County name as SVI spells it. *(derived)* |
| `population` | int64 | 100% | County population as carried in the SVI release. *(derived)* |
| `svi_overall` | float64 | 100% | CDC/ATSDR Social Vulnerability Index 2022 overall percentile rank (RPL_THEMES), 0 to 1. A percentile within the United States, so it is relative deprivation, not absolute. Static across the sampling window. *(derived)* |
| `svi_socioeconomic` | float64 | 100% | SVI theme 1 percentile rank: socioeconomic status. *(derived)* |
| `svi_household` | float64 | 100% | SVI theme 2 percentile rank: household characteristics. *(derived)* |
| `svi_minority_status` | float64 | 100% | SVI theme 3 percentile rank, as CDC/ATSDR names and constructs it. Carried through unchanged; this project does not use it as a standalone criterion for any decision. *(derived)* |
| `svi_housing_transport` | float64 | 100% | SVI theme 4 percentile rank: housing type and transportation. *(derived)* |

## `lots_synthetic.csv`

**SIMULATED** food-bank lot inventory. Every row carries is_synthetic = True. No real inventory data exists in this project.

`data/inventory/lots_synthetic.csv` · Rows: 1,880 · Columns: 16

| Column | Type | Non-null | Description |
|---|---|---|---|
| `lot_id` | object | 100% | Identifier for a SIMULATED lot. The prefix records the generator seed. *(derived)* |
| `is_synthetic` | bool | 100% | Always True. Present on every row so that no consumer of this table can mistake it for real food-bank inventory. *(derived)* |
| `establishment_id` | int64 | 100% | Establishment number normalised to an integer for joining to the MPI directory. FSIS recommends joining on this rather than on establishment_number, which can be reused over time. *(derived)* |
| `establishment_number` | object | 100% | Establishment mark of the real FSIS plant the simulated lot is attributed to. *(derived)* |
| `establishment_name` | object | 100% | Name of that real plant. *(derived)* |
| `source_state` | object | 100% | State of that plant. *(derived)* |
| `source_county` | object | 98% | County of that plant. *(derived)* |
| `haccp_size` | object | 100% | FSIS HACCP size category of that plant (Large, Small, Very Small). *(derived)* |
| `product_class` | object | 100% | Product category implied by project_code: chicken_carcass, chicken_parts, comminuted_chicken, turkey_carcass, comminuted_turkey, or an exploratory class. *(derived)* |
| `received_date` | object | 100% | SIMULATED date the lot arrived at the food bank. *(derived)* |
| `use_by_date` | object | 100% | SIMULATED use-by date. *(derived)* |
| `shelf_life_days` | int64 | 100% | SIMULATED shelf life in days, drawn per product class. Short for fresh carcass and parts, long for frozen comminuted and turkey. *(derived)* |
| `pounds` | float64 | 100% | SIMULATED weight of the lot. Not a measurement of anything. *(derived)* |
| `dest_county` | object | 100% | SIMULATED destination county, drawn weighted by vulnerability within the service state. *(derived)* |
| `dest_fips` | int64 | 100% | FIPS code of that destination county. *(derived)* |
| `dest_svi_overall` | float64 | 100% | svi_overall of the destination county. Real SVI, attached to a simulated destination. *(derived)* |

## `t20_scenarios_h3.csv`

One row per policy scenario: error rates, pounds, and both error types in meals.

`analysis/outputs/t20_scenarios_h3.csv` · Rows: 4 · Columns: 30

| Column | Type | Non-null | Description |
|---|---|---|---|
| `scenario` | object | 100% | Named policy: rule_based_category, conservative, capacity_matched or food_security_weighted. *(derived)* |
| `label` | object | 100% | Human-readable description of the scenario. *(derived)* |
| `lots` | int64 | 100% | Lots the scenario was evaluated on. *(derived)* |
| `lots_unscored` | int64 | 100% | Lots with no score within the staleness limit. These are distributed with the gap named, never assumed low risk. *(derived)* |
| `hold_at` | float64 | 75% | Probability threshold at or above which a lot is held. Horizon-specific: a threshold on an absolute probability does not transfer between forecast horizons. *(derived)* |
| `divert_at` | float64 | 75% | Probability threshold at or above which a lot is diverted to the cooked-meal channel. *(derived)* |
| `review_capacity_per_week` | float64 | 50% | Modelled number of lots the food bank can review per week. Null means unlimited. *(derived)* |
| `cook_capacity_lbs_per_week` | float64 | 75% | Modelled SIMULATED pounds the cooked-meal channel can absorb per week. Diverted pounds beyond it are discarded. *(derived)* |
| `food_security_weight` | float64 | 100% | 0 to 1. Raises the hold and divert thresholds for destinations in the most vulnerable SVI quartile, protecting supply there at the cost of accepting more risk there. *(derived)* |
| `n_distribute_now` | int64 | 100% | Lots recommended for normal distribution. *(derived)* |
| `n_prioritize` | int64 | 100% | Lots recommended for immediate distribution, because little shelf life remains. *(derived)* |
| `n_hold_for_review` | int64 | 100% | Lots recommended for review. High-consequence. *(derived)* |
| `n_divert` | int64 | 100% | Lots recommended for the cooked-meal channel. High-consequence. *(derived)* |
| `precision` | float64 | 100% | Of the lots held or diverted, the share from plants that did go on to elevated risk. *(derived)* |
| `recall` | float64 | 100% | Of the lots from plants that went on to elevated risk, the share held or diverted. *(derived)* |
| `tp` | int64 | 100% | Held or diverted, and the plant did go on to elevated risk. *(derived)* |
| `fp` | int64 | 100% | Held or diverted, and the plant did not. *(derived)* |
| `fn` | int64 | 100% | Distributed, and the plant did go on to elevated risk. *(derived)* |
| `tn` | int64 | 100% | Distributed, and the plant did not. *(derived)* |
| `pounds_distributed` | float64 | 100% | SIMULATED pounds distributed, including lots moved early. *(derived)* |
| `pounds_held` | float64 | 100% | SIMULATED pounds held for review. *(derived)* |
| `pounds_diverted` | float64 | 100% | SIMULATED pounds sent to the cooked-meal channel. *(derived)* |
| `pounds_discarded` | float64 | 100% | SIMULATED pounds lost, from a hold that exhausted the shelf life or from diversion beyond the cooked channel's capacity. *(derived)* |
| `avoidable_loss_lbs` | float64 | 100% | SIMULATED pounds discarded from plants that did NOT go on to elevated risk: the cost of a false alarm. *(derived)* |
| `avoidable_loss_meals` | int64 | 100% | avoidable_loss_lbs at 1.2 lb per meal, Feeding America's convention. *(derived)* |
| `exposure_lbs` | float64 | 100% | SIMULATED pounds distributed uncooked from plants whose sampling later deteriorated. NOT a count of illnesses and not an estimate of one; FSIS data cannot attribute illness to an establishment. *(derived)* |
| `exposure_meals` | int64 | 100% | exposure_lbs at 1.2 lb per meal. *(derived)* |
| `holds_per_week_required` | float64 | 100% | Reviews per week the scenario demands. Compared against review capacity to show whether a policy is executable at all. *(derived)* |
| `review_capacity_exceeded_by` | float64 | 50% | holds_per_week_required divided by review capacity. Above 1 means the policy cannot be run as written. *(derived)* |
| `pounds_are_synthetic` | bool | 100% | Always True. Marks the row as resting on simulated inventory. *(derived)* |

## `t21_equity_by_svi_quartile_h3.csv`

Distribution and withholding by destination SVI quartile, per scenario.

`analysis/outputs/t21_equity_by_svi_quartile_h3.csv` · Rows: 16 · Columns: 9

| Column | Type | Non-null | Description |
|---|---|---|---|
| `svi_quartile` | object | 100% | Quartile of destination county svi_overall, fixed once so every scenario is measured against the same bins. *(derived)* |
| `scenario` | object | 100% | Named policy: rule_based_category, conservative, capacity_matched or food_security_weighted. *(derived)* |
| `lots` | int64 | 100% | Lots the scenario was evaluated on. *(derived)* |
| `pounds_offered` | float64 | 100% | SIMULATED pounds destined for that quartile before any policy is applied. *(derived)* |
| `pounds_distributed` | float64 | 100% | SIMULATED pounds distributed, including lots moved early. *(derived)* |
| `pounds_withheld` | float64 | 100% | SIMULATED pounds held or diverted away from that quartile. *(derived)* |
| `withheld_pct` | float64 | 100% | pounds_withheld as a share of pounds_offered, per quartile. The disparity check compares the most and least vulnerable quartiles and reports the result whichever way it comes out. *(derived)* |
| `share_of_all_distribution_pct` | float64 | 100% | That quartile's share of all distributed pounds. *(derived)* |
| `pounds_are_synthetic` | bool | 100% | Always True. Marks the row as resting on simulated inventory. *(derived)* |

## `t22_frontier_h3.csv`

Threshold sweep: the trade-off between avoidable loss and exposure.

`analysis/outputs/t22_frontier_h3.csv` · Rows: 15 · Columns: 9

| Column | Type | Non-null | Description |
|---|---|---|---|
| `hold_at` | float64 | 100% | Probability threshold at or above which a lot is held. Horizon-specific: a threshold on an absolute probability does not transfer between forecast horizons. *(derived)* |
| `divert_at` | float64 | 100% | Probability threshold at or above which a lot is diverted to the cooked-meal channel. *(derived)* |
| `recall` | float64 | 100% | Of the lots from plants that went on to elevated risk, the share held or diverted. *(derived)* |
| `precision` | float64 | 100% | Of the lots held or diverted, the share from plants that did go on to elevated risk. *(derived)* |
| `pounds_distributed` | float64 | 100% | SIMULATED pounds distributed, including lots moved early. *(derived)* |
| `pounds_discarded` | float64 | 100% | SIMULATED pounds lost, from a hold that exhausted the shelf life or from diversion beyond the cooked channel's capacity. *(derived)* |
| `avoidable_loss_meals` | int64 | 100% | avoidable_loss_lbs at 1.2 lb per meal, Feeding America's convention. *(derived)* |
| `exposure_meals` | int64 | 100% | exposure_lbs at 1.2 lb per meal. *(derived)* |
| `pounds_are_synthetic` | bool | 100% | Always True. Marks the row as resting on simulated inventory. *(derived)* |

## `t23_lot_actions_h3.csv`

Per-lot recommendation for the default scenario, with reversal evidence.

`analysis/outputs/t23_lot_actions_h3.csv` · Rows: 1,880 · Columns: 27

| Column | Type | Non-null | Description |
|---|---|---|---|
| `lot_id` | object | 100% | Identifier for a SIMULATED lot. The prefix records the generator seed. *(derived)* |
| `is_synthetic` | bool | 100% | Always True. Present on every row so that no consumer of this table can mistake it for real food-bank inventory. *(derived)* |
| `establishment_id` | int64 | 100% | Establishment number normalised to an integer for joining to the MPI directory. FSIS recommends joining on this rather than on establishment_number, which can be reused over time. *(derived)* |
| `establishment_number` | object | 100% | Establishment mark of the real FSIS plant the simulated lot is attributed to. *(derived)* |
| `establishment_name` | object | 100% | Name of that real plant. *(derived)* |
| `product_class` | object | 100% | Product category implied by project_code: chicken_carcass, chicken_parts, comminuted_chicken, turkey_carcass, comminuted_turkey, or an exploratory class. *(derived)* |
| `received_date` | object | 100% | SIMULATED date the lot arrived at the food bank. *(derived)* |
| `use_by_date` | object | 100% | SIMULATED use-by date. *(derived)* |
| `days_left` | int64 | 100% | Shelf-life days remaining when the lot arrived. *(derived)* |
| `pounds` | float64 | 100% | SIMULATED weight of the lot. Not a measurement of anything. *(derived)* |
| `dest_county` | object | 100% | SIMULATED destination county, drawn weighted by vulnerability within the service state. *(derived)* |
| `dest_svi_overall` | float64 | 100% | svi_overall of the destination county. Real SVI, attached to a simulated destination. *(derived)* |
| `svi_quartile` | object | 100% | Quartile of destination county svi_overall, fixed once so every scenario is measured against the same bins. *(derived)* |
| `category` | float64 | 87% | FSIS Salmonella Category 1, 2, 3 or NA, rebuilt from raw samples on the 52-week moving window by fsis_categories.py. Validated against three official postings at 99.75% agreement over 2,764 rows. *(derived)* |
| `n52` | float64 | 87% | Routine samples in the 52-week window. *(derived)* |
| `pos52` | float64 | 87% | Routine positives in the 52-week window, counted the way FSIS counts for categorisation. *(derived)* |
| `projection` | float64 | 87% | Binomial projection of the probability the unit enters Category 3 within the forecast horizon. The transparent baseline scorer, and the default in the decision layer at short horizons because it is the better calibrated there. *(derived)* |
| `scored` | bool | 100% | Whether a score within the staleness limit was available for the lot's plant and product class. *(derived)* |
| `score_age_days` | float64 | 87% | Days between the score's window_end and the lot's arrival. Lots join to scores with a backward as-of join, so a lot only knows what was published before it arrived. *(derived)* |
| `action` | object | 100% | distribute_now, prioritize, hold_for_review or divert. *(derived)* |
| `driver` | object | 100% | One sentence naming the signal that produced the action. *(derived)* |
| `high_consequence` | bool | 100% | True for hold and divert. These require explicit human confirmation and carry reversal evidence. *(derived)* |
| `requires_human_confirmation` | bool | 100% | True wherever high_consequence is true. Nothing is executed automatically. *(derived)* |
| `alternative_action` | object | 100% | The opposite action, offered with its own cost so the user sees a choice rather than a verdict. *(derived)* |
| `reversal_evidence` | object | 17% | What would change this recommendation, named per lot. *(derived)* |
| `discarded` | bool | 100% | True when the lot was lost under this policy. *(derived)* |
| `discard_reason` | object | 2% | Which of the two loss mechanisms applied: a review hold that exhausted the shelf life, or the cooked-meal channel being at capacity. *(derived)* |
