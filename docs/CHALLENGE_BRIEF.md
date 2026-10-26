# SENS-D challenge brief: what the organizers actually require

**Source:** Pedro Ramonetti Vega, 2026-10-26 13:28 CT, by email to the team, linking
<https://docs.google.com/document/d/1MjCMemLzY3FSlqLAnPBCcM0u22Vw5wpm/edit>

> **This file is an extracted summary, not the brief verbatim.** The original is a Google Doc that
> could not be copied in full. Every requirement below was read out of that document, but the wording
> is not the organizers'. **Before the report is written, one of us must open the original and check
> this file against it line by line.** Where the two disagree, the Google Doc wins.

Until 2026-10-26 the challenge page carried no description, no goal and no dataset details, and the
organizers have acknowledged a website fault. Everything built before this date was inferred from the
track title, and some of it was aimed at the wrong user. See "What this changed" at the end.

---

## The challenge question

> How can a supply-chain actor anticipate emerging food-safety risk and make proactive decisions that
> protect health while preserving food availability, supporting food security, and minimizing
> avoidable food loss?

Full framing: a **proactive One Health decision-support tool for food safety and food security**. The
anchor case is Salmonella and other hazards in FSIS-regulated perishable foods, poultry as the key
commodity.

## The decision-maker

**Team-selected, one of:** processor, distributor or logistics operator, retailer, or regional food
bank. This is a choice the team makes and must justify. It is *not* a regulator, which is what this
project assumed before the brief appeared.

---

## Required data

| Source | Notes |
|---|---|
| **CDC PulseNet**, or an organizer-provided extract | Human-health and genomic surveillance. Organizers may substitute an approved aggregate **or a public CDC human-illness dataset**. |
| **USDA FSIS public data** | Sampling, establishment information, pathogen results, **recalls and public health alerts**. Sampling or WGS identifiers alone cannot establish causal links to illness. |
| **NOAA/NCEI Climate Data Online** | Weather and climate. Requires a free API token. |
| **At least two team-added external datasets** | At least one must cover food security, population vulnerability, supply chain, animal health, environmental exposure, or infrastructure. Suggested: USDA food-access and food-security data, Census ACS, CDC/ATSDR SVI, wastewater, transportation networks, actor operational data. |

Every dataset needs documented provenance, licensing, resolution, missingness, update frequency and
**decision value**.

---

## The five required tasks

All are required and they build on each other.

**1. Define the system and data layer.** Choose the actor and the decision. Build a One Health system
map. Align datasets. Produce a data dictionary and provenance table. Write a decision statement.

**2. Build and validate a risk model.** Predict near-term elevated risk at a decision-relevant unit.
Requires: a transparent baseline, an integrated model, time-aware validation, **discrimination and
calibration** metrics, uncertainty analysis, and the **marginal value of each added data source**.

**3. Convert predictions into decisions.** Define feasible actions and constraints (inventory,
perishability, transport, storage, need). Include a **food-security or equity objective**. Compare
against a **rule-based policy**. Run **at least three scenarios**. Require **human review for
high-consequence actions**.

**4. Build the app with AWS Kiro.** Use Kiro specs and steering files. Interactive web app, React
recommended. Must include five things:
- a current-risk view
- an alert queue
- a scenario builder
- a recommended-action panel
- an evidence panel that exposes uncertainty

**5. Team science.** Document roles. Add at least two datasets. Run an **ablation** showing the effect
of the added data. Record a **decision changed by another discipline**. Name the next dataset or
partner to add.

---

## Evaluation weights

| Criterion | Weight |
|---|---|
| Data science rigor and validation | 25% |
| Operational decision support | 25% |
| One Health and multi-source integration | 20% |
| Kiro implementation and usability | 15% |
| Team science, reproducibility and communication | 15% |

---

## The ten report questions

The PDF report must address:

1. The decision-maker and the decision horizon
2. The role of each core dataset
3. The added datasets and their impact
4. The modeled outcome
5. Performance against the baseline
6. Which errors are costly: false alarms against missed risk
7. Where food safety and food security conflict
8. An end-to-end scenario
9. The effect of team science on the work
10. What the tool can and can never claim, and what deployment would require

---

## Deliverables, in the GitHub repository

1. Reproducible analysis notebooks or scripts
2. Kiro specs, prompts, steering files and hooks, disclosing substantial manual edits
3. Runnable web app with build and deployment instructions
4. Data dictionary and provenance file
5. PDF report: methods, metrics, figures, scenarios, limitations, team science statement
6. README and requirements

---

## Guardrails, stated by the organizers

- The tool is a **prototype**, not a regulatory determination, not an outbreak declaration, and not a
  substitute for epidemiologic investigation.
- Expose uncertainty, provenance and the driving signals.
- Include human review, and identify the evidence needed, for high-consequence actions.
- **Never label a food, establishment or shipment "safe" or "unsafe" on the model alone.**
- Test whether recommendations unfairly disadvantage high-need communities.

---

## What this changed for us

Work that transfers unchanged:

- The FSIS pipeline, the category rebuild validated at 99.75%, and provenance
- The transparent baseline against an integrated model: binomial projection AUROC 0.917 against
  gradient boosting 0.926, which is exactly the Task 2 comparison
- Time-aware validation and establishment-clustered bootstrap uncertainty
- The comparison against the current Category 2 flag, which is the required rule-based policy baseline
- NORS as the human-illness layer. The brief permits "a public CDC human-illness dataset" in place of
  PulseNet, and NORS is one

Work that has to change:

- **The user.** Everything was framed for a regulator allocating inspections. It must be a
  supply-chain actor.
- **Missing required data:** NOAA/NCEI climate, FSIS recalls and alerts, and two team-added datasets
- **Missing analysis:** reliability for the default scorer and a reliability figure (Brier and a
  gradient-boosting table already exist), the leave-one-source-out ablation, two more scenarios
- **Missing objective:** food security, equity, and avoidable food loss appear nowhere yet
- **Missing artifact:** the One Health system map
- **App structure:** the five named components above, with human review built in
