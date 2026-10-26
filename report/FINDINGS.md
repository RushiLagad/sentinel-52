# Findings: evidence, not prose

**This file is source material for the report, not a draft of it.** The report narrative is the
team's own work. What follows is the claim, the numbers behind it, where each number comes from, and
— most importantly — what the evidence does *not* support, so nobody overstates it under deadline.

Every figure here traces to a named file in `analysis/outputs/`. If a number is not in one of those
files, it does not go in the report.

---

## Finding 1: What sampling finds is not what sends people to hospital

**Figure:** `analysis/outputs/figures/fig5_prevalence_vs_burden.png`
**Tables:** `t17_chicken_prevalence_vs_burden.csv`, `t16_nors_poultry_burden_by_serotype.csv`
**JSON:** `burden_weighting.json`

### The numbers

Chicken, FSIS serotyped isolates in FY2026 against NORS outbreak-associated hospitalizations
2014–2023:

| Serotype | Share of isolates | Hospitalizations | In FSIS FY22–26 indicator |
|---|---|---|---|
| Infantis | 36.1% | 31 | yes |
| Enteritidis | 22.8% | 184 | yes |
| **Kentucky** | **16.6%** | **0** | no |
| Typhimurium | 10.2% | 22 | yes |

Infantis rose from 3.5% of serotyped chicken isolates in FY2015 to 36.1% in FY2026, and carries
86.2% multidrug resistance across 1,996 isolates (`t13_fsis_wgs_resistance_by_serotype.csv`).
Kentucky fell from 40.1% to 16.6% over the same period and carries 3.3% MDR across 1,259 isolates.

### The policy half

`burden_weighting.json`, poultry-attributed outbreaks 2014–2023:

- **Chicken:** the three serotypes in the withdrawn 2024 proposed framework account for **65.7%** of
  chicken-attributed hospitalizations. The highest-burden chicken serotype, Enteritidis, is on both
  the framework list and the indicator.
- **Turkey:** the three framework serotypes account for **6.8%**. The highest-burden turkey serotype
  is **Reading**, which appears on neither list.

### What this does NOT support

- **It does not say FSIS chose wrong.** For chicken the lists capture two thirds of the burden. Report
  that half as prominently as the turkey half, or the analysis is selective rather than rigorous.
- **It does not say Kentucky is harmless.** Zero *outbreak-associated* hospitalizations in NORS is not
  zero illness. Most salmonellosis is sporadic and never enters NORS at all.
- **Reading's 135 turkey hospitalizations are 98.5% from one 2017 multistate outbreak.** This is an
  argument for lists that adapt, not evidence that Reading is permanently the top turkey threat.
  Typhimurium's 22 come from a single outbreak, Infantis's 31 are 80.6% from one. Enteritidis at 27%
  from its largest is the only poultry serotype whose figure rests on a broad base (62 outbreaks).
  **Never quote any of these without the single-outbreak share beside it.**
- **Attribution is incomplete.** 710 of 1,284 Salmonella foodborne outbreaks carry no IFSAC food
  category, covering 1,891 of 5,846 hospitalizations, which is 32.3%. Poultry-attributed burden is a
  floor, not an estimate.
- **The series do not end together.** Public NORS runs to 2023; FSIS sampling to FY2026.
- **No establishment is linked to any illness.** Every join is serotype × year, as the FSIS licence
  requires.

---

## Finding 2: The transparent baseline is the model's most valuable feature, and its worse-calibrated scorer

Two separate results that point in opposite directions. Both belong in the report; reporting either
alone would be misleading.

### 2a. Most valuable feature

**Table:** `t19_ablation_h6.csv` · **JSON:** `ablation_h6.json` (also h3, h12)
**Script:** `05d_ablation.py`, leave-one-group-out, establishment-clustered bootstrap

Dropping the binomial projection costs more AUROC than dropping the entire sampling-history group:

| Dropped | ΔAUROC 3mo | ΔAUROC 6mo | 12mo |
|---|---|---|---|
| Binomial projection | −0.0095 | −0.0075 | −0.0021 (noise) |
| Sampling history | — | −0.0067 | −0.0120 |
| Everything beyond FSIS core | −0.0074 | −0.0074 | −0.0013 (noise) |

Everything beyond basic sampling and category position buys under 0.01 AUROC in total.

### 2b. Worse calibrated

**Figure:** `analysis/outputs/figures/fig4_reliability_h6.png`
**Table:** `t18_reliability_h6.csv` · **JSON:** `calibration_h6.json`

| Scorer | Brier | ECE | Top decile predicted vs observed |
|---|---|---|---|
| Binomial projection | 0.0426 | **0.0092** | 0.465 vs 0.416 |
| Gradient boosting | 0.0417 | **0.0045** | 0.432 vs 0.426 |

The projection under-states risk across the lower eight deciles and over-states it at the top. For a
food bank that is the worst combination available: over-holding at the top is avoidable food loss,
under-flagging in the middle is missed risk in the band you would distribute without review.

It also emits **exactly zero** for 74 test rows, two of which went on to fail. A probability of
literally zero is never defensible and needs a floor.

### What this does NOT support

- **It does not justify switching to gradient boosting.** The AUROC gap is 0.917 vs 0.926 with heavily
  overlapping intervals, and the projection is arithmetic a reviewer can reproduce by hand. ECE 0.0092
  is still small in absolute terms.
- **It does not mean the model is well calibrated everywhere.** Both scorers deviate at very low
  probabilities. That band happens not to drive decisions, which is a reason to say so explicitly
  rather than to ignore it.
- **The honest framing is a caveat, not a reversal:** keep the transparent scorer, report that it is
  the less well calibrated of the two, and either floor it or recalibrate it.

---

## Finding 3: Serotype detail adds nothing predictive, and that is the point

**Table:** `t19_ablation_h6.csv`

Dropping serotype features is within noise at every horizon and sometimes slightly improves the
model (+0.0009 AUROC at 6 months).

This is not a contradiction of Finding 1. The FSIS category counts positives and is blind to which
serotype they were, so serotype cannot help predict it. Serotype governs **consequence**, which NORS
measures, not **compliance**, which the category measures. The null result is evidence that the
current system ignores information, which is the argument.

Also worth reporting: at 3 months, dropping the CFU enumeration group **improves** the model
(+0.0031 AUROC, distinguishable from zero). A source that hurts is a result.

---

## Still to be established

These are not findings yet and must not be written as if they were:

- Anything denominated in pounds, meals or food loss. The inventory layer is **simulated**.
- Any climate effect. NOAA data is not in yet, and month-of-year is already within noise, so the
  prior should be that climate adds little to *this* outcome.
- Any equity or disparity claim. SVI and food access are not in yet.
- Any recall-to-establishment history. Marks are recoverable for only 36.6% of relevant recalls, so
  an establishment with no linked recall may simply be unresolvable.
