# Findings: evidence, not prose

**This file is source material for the report, not a draft of it.** The report narrative is the
team's own work. What follows is the claim, the numbers behind it, where each number comes from, and
and, most importantly, what the evidence does *not* support, so nobody overstates it under deadline.

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
| Sampling history | n/a | −0.0067 | −0.0120 |
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

## Finding 3: Serotype detail adds nothing predictive, which is itself informative

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

---

## Finding 4: The status quo cannot actually be run, and approximating it costs food

**Table:** `t20_scenarios_h3.csv` · **JSON:** `decision_layer_h3.json`
**Frontier:** `t22_frontier_h3.csv` · **Equity:** `t21_equity_by_svi_quartile_h3.csv`
**Script:** `16_decision_layer.py`, horizon 3 months, scorer chosen by measured calibration

**Read the caveats below before quoting any number here.** Every poundage is simulated.

**Independently reproduced, 2026-10-27.** This table was produced twice, from two separate builds of
`data/processed` on two machines, and every figure matched to the digit: lot counts, precision,
recall, pounds, meals, the dominance relation, and all four disparity values. The h3 *ablation*
verdicts do shift between those same two builds (Finding 2), which is why none are quoted here. The
decision layer does not shift.

**Reproduced.** This table was produced twice, on two machines and two separate builds of
`data/processed` (Linux/Python 3.13 and Windows/Python 3.12, 2026-10-27), and every figure below
matched to the digit: all sixteen counts, all eight rates, all four meal totals, the dominance
relation and all four disparity values. The one part of the pipeline that did *not* reproduce
across the two runs is the **h3 ablation**, whose marginal verdicts flip (see Finding 2); the h6
ablation matched exactly. Quote h6 ablation verdicts, not h3 ones.

### Why 3 months, and why the scorer is not fixed

The decision is taken inside a lot's perishability window, so the nearest forecast horizon is the
relevant one. There is also a data reason, which we did not anticipate: **80% of lots have a usable
score at h3 against 64% at h6**, because the h6 test window ends six months earlier and more lots
fall outside the staleness limit. An unscored lot gets distributed with the gap named, so coverage
feeds straight into recall. Run at h6, the conservative policy reaches recall 0.272 and destroys
62,042 meals; at h3 it reaches 0.403 and destroys 30,529. h3 is better on both axes at once.

The scorer is therefore *not* hardcoded. `16_decision_layer.py` reads `calibration_h{H}.json` and
takes whichever scorer has the lower expected calibration error at the horizon it is run at:
the projection at h3 (ECE 0.0056 against 0.0222), gradient boosting at h6 (0.0092 against 0.0045).
An earlier version hardcoded the projection and `run_all.py` then ran it at h6, which used the
worse-calibrated scorer at that horizon. Both are fixed.

### The numbers

Four policies on the same 1,880 simulated lots from 52 real establishments, 3.25M simulated lb,
33 Arkansas destination counties, over 52 weeks:

| Policy | Recall | Precision | Holds/week | Avoidable loss (meals) | Exposure (meals) |
|---|---|---|---|---|---|
| Rule-based: hold anything Category 2 or 3 | 1.000 | 0.305 | **13.4** | **108,499** | 0 |
| Conservative: hold at projection ≥ 0.05 | 0.403 | 0.280 | 3.6 | 30,529 | 213,046 |
| Capacity-matched: threshold set to fill 6 reviews/week | 0.407 | 0.242 | 4.6 | 46,975 | 212,118 |
| Food-security weighted: same, high-need supply protected | 0.407 | 0.249 | 4.6 | 42,004 | 212,118 |

The status quo catches everything in this supply base. It does so by holding 38% of incoming lots,
which is **13.4 reviews a week against a modelled capacity of 6**, and by destroying 108,499 meals
of edible food, and 91% of that discard comes from plants that never went on to elevated risk.

### Three things follow

**1. The argument for the tool is feasibility rather than accuracy.** We are not claiming to out-predict
the FSIS category. On this supply base the category rule has perfect recall. The claim is that it
cannot be run at the capacity a food bank actually has, and that what it costs to approximate it by
holding everything is measured in meals.

**2. Review capacity is not the binding constraint. Shelf life is.** Setting the threshold to fill
the review queue to capacity *loses to* the simpler conservative threshold: +0.4 points of recall
for 54% more food destroyed, because every extra hold consumes shelf life that some lots do not
have. `16_decision_layer.py` reports this as a dominance relation rather than burying it:
`capacity_matched` is dominated by `food_security_weighted`, which reaches identical recall while
destroying 4,971 fewer meals. Using capacity because it is there is the wrong instinct.

**3. Food-security weighting is close to free here, and that is not a general result.** Requiring a
stronger signal before withholding from the most vulnerable SVI quartile moves the withheld-share
gap from −0.34 to −2.66 percentage points and cuts loss by 4,971 meals at identical recall. It is
close to free *in this simulation* because the destinations that get protected are not the ones
supplied by the riskiest plants. Where those overlap, the trade would be real, and the tool shows
the gap rather than optimising it away.

### What this does NOT support

- **Any statement about a real food bank's poundage.** Lots, pounds, destinations and shelf life are
  generated by `14_build_synthetic_inventory.py` from a seeded procedure. The ranking, the error
  rates and the direction of the equity effect do not depend on the simulation's scale. The absolute
  pounds and meals depend on it entirely and are not measurements.
- **Any claim about the risk model's accuracy.** These are a *policy's* error rates on 52
  high-volume suppliers. The model's own metrics, on the full 578-establishment panel, are in
  `early_warning_summary_h*.json`. The rule-based recall of 1.000 here is a property of this narrow
  supply base: on the full 582-establishment panel **at the same 3-month horizon**, script 05
  measures the Category 2 flag at recall 0.915 and precision 0.145. (An earlier draft of this
  sentence quoted 0.813, which is the h6 figure. The decision layer runs at h3, so h3 is the
  comparison that belongs here.)
- **Any illness claim.** "Exposure" is food distributed uncooked from plants whose *sampling* later
  deteriorated. It is not a count of illnesses, nor an estimate of one. The FSIS licence forbids
  attributing illness to an establishment and nothing in this project does.
- **A stable scenario ranking.** `hold_at` and `divert_at` are thresholds on an absolute
  probability, so they are horizon-specific and do not transfer: at h3 `capacity_matched` is
  dominated by `food_security_weighted`, and at h6 the dominance runs the other way. The script
  recomputes dominance per run and reports it; it is a property of the run, not a conclusion about
  the policies.
- **A recommended operating point.** `t22_frontier_h3.csv` is not convex: avoidable loss falls from
  61,095 to 8,861 meals and then rises again as the threshold climbs, because raising the divert
  threshold pushes lots back into holds, where shelf life kills them. There is no clean optimum, and
  choosing between 61,095 meals destroyed and 30,000 more meals of exposure is a judgement about
  whose risk counts. The tool declines to make it.

---

## Still to be established

These are not findings yet and must not be written as if they were:

- Anything denominated in pounds, meals or food loss. The inventory layer is **simulated**.
- Any climate effect. NOAA GSOM monthly data is now in `data/noaa/` but is not yet a model
  feature, and month-of-year is already within noise in the ablation, so the prior should be
  that climate adds little to *this* outcome.
- Any equity claim resting on **food access**. CDC/ATSDR SVI 2022 is in and the disparity check
  runs on it (Finding 4), but the USDA food-access layer and the ACS population join are not:
  the Census API key was rejected, so `vulnerability_county.csv` is SVI alone. County is also a
  coarse proxy for a service area.
- Any recall-to-establishment history. Marks are recoverable for only 36.6% of relevant recalls, so
  an establishment with no linked recall may simply be unresolvable.
