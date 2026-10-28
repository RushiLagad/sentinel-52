# Sentinel-52 handoff

**Read this first if you are an AI assistant, a new collaborator, or returning after a break.**
Everything here is current as of commit `68f1de7`, 2026-10-28. Where this file and the code
disagree, the code is right and this file is stale: say so rather than working from it.

---

## 1. What this is, and when it is due

Team **Sentinel-52** (Rushikesh Lagad, University of Arkansas; Sambhavi Patel, UARK;
Naisargi Modha, Northeastern) is entering the **Fall 2026 NAFSI Hub Student Data Challenge,
SENS-D track**.

**Deadline: Monday 2026-11-02, 16:00 US Central.** A push to the repository after that
disqualifies the team. The hub's team panel says "November 1" somewhere; the brief says the 2nd.
Treat the earlier as the working deadline.

Repository: `github.com/RushiLagad/sentinel-52`.
The brief as published is in `docs/CHALLENGE_BRIEF.md`. **That file is a summary, not verbatim.**
Task 5.7 is to check it line by line against Pedro's original Google Doc, and it is still open. Do
not treat it as authoritative for anything load-bearing until that is done.

Grading weights: 25% analytical rigor, 25% operational relevance, 20% One Health integration,
15% Kiro usage, 15% team science.

---

## 2. The decision this tool supports

The brief asks for one supply-chain actor. We chose a **regional food bank**, because the brief's
three secondary objectives (food availability, food security, minimizing avoidable food loss) are
a food bank's mission rather than side constraints, and they collide daily with protecting health.

> **Decision statement.** For each incoming or on-hand lot of FSIS-regulated poultry, the food bank
> must decide within its perishability window whether to **distribute now**, **prioritize for
> immediate distribution**, **hold for review**, or **divert**, given the producing establishment's
> near-term risk, the nutritional need of the communities it serves, and the loss created by
> discarding edible food.

The mechanism: the USDA mark of inspection carries the establishment number, so a pallet traces to
a plant with a public sampling history.

**Divert means the cooked-meal channel, not the bin.** A plant with a deteriorating sampling
trajectory does not make its product inedible; it makes uncooked distribution the wrong channel.
That is the actor-specific move that makes the health-versus-loss tension resolvable at all.

Full reasoning: `.kiro/specs/onehealth-decision-support/{requirements,design,tasks}.md`.

---

## 3. Hard rules. Breaking any of these is worse than missing a deadline.

1. **The FSIS licence forbids linking establishments to illness.** The data "should not be used to
   identify foodborne illness outbreaks, associate samples with foodborne illness outbreaks or
   determine whether two or more samples are causally related." Every join between FSIS sampling
   and CDC NORS is made at **serotype × year**, never at establishment level. No code in this
   repository constructs that link, and `fig6_one_health_system_map.png` draws it crossed out so a
   reader finds the absence labelled rather than wondering.
2. **The inventory is simulated.** There is no real food-bank inventory anywhere in this project.
   `14_build_synthetic_inventory.py` generates it from a seeded procedure. Every row carries
   `is_synthetic = True`, every pounds- or meals-denominated payload is declared in
   `app/public/data/meta.json`, and the app must badge every such figure. A reader who believes
   those pounds are real has been misled.
3. **Nothing is a safety verdict.** No output says any food, lot or establishment is safe or unsafe.
   This tool ranks what to look at first and shows the evidence. A person decides.
4. **Nothing executes automatically.** Hold and divert are high-consequence: they require explicit
   human confirmation and carry per-lot reversal evidence.
5. **The report narrative is the team's own work.** AI generates code, figures, tables and
   docstrings. It does not write the report prose.
6. **Organizers emailed the team restricted NORS and FSIS RTE files** with "please do not share
   them with anyone outside your team." Those files must never enter the repository. The NORS data
   the pipeline uses comes from the **public** CDC Socrata endpoint instead.

---

## 4. How to reproduce everything

```bash
git clone https://github.com/RushiLagad/sentinel-52 && cd sentinel-52
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt                        # openpyxl is needed and is easy to skip
cd analysis
python scripts/01_fetch_fsis.py --print-urls           # 31 FSIS files and where each goes
# download them into data/raw/<folder>/<name>, then:
python run_all.py                                      # verifies hashes, then builds everything
```

**`--download` is unreliable and that is not a bug in our code.** Since 2026-10-27 the FSIS CDN
returns HTTP 403 to automated requests, though the files are unchanged and still public at the URLs
in `data/MANIFEST.json` (verified in a browser the same day). Manual download plus
`--verify-only` gives an identical SHA-256 check, so it is not weaker provenance.

The decision layer additionally needs `data/vulnerability/vulnerability_county.csv`, built by
`13_fetch_vulnerability.py`, which needs network access to `svi.cdc.gov`. `run_all.py` skips the
decision layer with an explanation rather than failing if it is absent.

Runtime is about three minutes on one core. **The pipeline is deterministic.** Two runs on
identical input produce byte-identical output; we checked.

---

## 5. What is done

**Phase 1, data (6 of 8).** FSIS pipeline (scripts 01–08) validated: the Category 1/2/3/NA rebuild
agrees with three official FSIS postings on **99.75% of 2,764 rows with zero false Category 3s**.
NORS burden (09, 10), NOAA GSOM climate (11), FSIS recalls (12), SVI (13, partial), synthetic
inventory (14), the One Health system map figure (18).

**Phase 2, model (3 of 4).** Calibration (05c) and leave-one-group-out ablation with
establishment-clustered bootstrap (05d), at horizons 3, 6 and 12.

**Phase 3, decision layer (6 of 6).** `16_decision_layer.py`. Complete and independently
reproduced on two machines.

**Phase 4, app (1 of 13).** `17_build_app_data.py` and `app/public/data/*.json` only.

**Hooks: all four.** `.kiro/hooks/h1`–`h4`.

---

## 6. What is left, and where the risk is

**The app is the whole risk.** Twelve of the twenty-four open items are Phase 4, they carry a large
share of the operational-relevance score, and **not one line has been written.** Nothing else
should take priority over 4.2.

| Phase | Open | Notes |
|---|---|---|
| 1 | 1.3, 1.5, 1.6, 1.8 | 1.6 is half-built; see §8 |
| 2 | 2.1 | Reframed; see §7, finding 2 |
| 4 | **4.2–4.13** | Nothing started. Start at 4.2 and stop for review before building components. |
| 5 | 5.1–5.7 | Report. **5.7 is the highest-value hour anyone can spend** and needs no code. |

Task 5.2, "record a decision changed by another discipline **as it happens, not retrofitted**",
is time-sensitive by construction. If one has happened and nobody wrote it down, it is gone.

---

## 7. Findings, with the numbers and where they come from

Full evidence, with a "what this does NOT support" section on each: `report/FINDINGS.md`.

**1. What sampling finds is not what sends people to hospital.** Infantis went from 3.5% of
serotyped chicken isolates in FY2015 to **36.1%** in FY2026 while Kentucky fell 40.1% → 16.6%.
**86.2%** of chicken Infantis isolates are resistant to three or more drug classes against **3.3%**
for the Kentucky it displaced (FSIS WGS calls, FY2024–26). FSIS's own FY2022–26 indicator is
**5.78%** against a recomputed 4.20% baseline and a 3.80% target, which is above its baseline, not
10% below it.

**2. The transparent baseline carries the signal; most of what we added does not.** At the 6-month
horizon only three feature groups are distinguishable from noise: sampling history (−0.0073 AUROC),
the projection (−0.0064), and everything-beyond-core together (−0.0066). Serotype detail, other
pathogens, follow-up program, establishment profile, seasonality and product class are all within
noise. **This is why 2.1 was reframed**: climate, burden, recalls and vulnerability go into the
*decision layer*, where they weigh consequence and equity, not into the risk model, where they do
not move AUROC. "We tested whether these helped and they didn't, so we used them where they do" is
a stronger answer than a longer feature table.

**3. The status quo cannot actually be run, and approximating it costs food.** Holding anything
from a Category 2 or 3 plant reaches **recall 1.000** on this supply base. It does so by holding 38%
of incoming lots, which means **13.4 reviews a week against a modelled capacity of 6**, and by
destroying
**108,499 meals** of edible food, 91% of it from plants that never deteriorated. A threshold policy
catches 40% of the same risk for a quarter of the loss. Our argument is feasibility, not accuracy.

Two corollaries: **review capacity is not the binding constraint, shelf life is** (filling the
review queue buys +0.4 points of recall for 54% more food destroyed); and **food-security
weighting** moves the withheld-share gap from −0.34 to −2.66 percentage points at identical recall,
but only because the protected destinations are not the ones fed by the riskiest plants. Where
those overlap the trade would be real, so the frontier is shown rather than optimised.

---

## 8. Traps. Each of these has already cost time once.

- **Do not quote any h3 ablation verdict.** The h3 verdicts flip between two builds of the same
  data (`standard_position` reads "carries signal" on one and "within noise" on the other) because
  h3 has 644 new failures against h6's 979 and the bootstrap intervals are wider. **h6 reproduces
  byte-identically across machines. Quote h6 only.** The decision layer, by contrast, reproduces
  exactly at h3.
- **Scorer choice depends on the horizon.** The projection is far better calibrated at h3
  (ECE 0.0056 vs 0.0213) and worse at h6 (0.0092 vs 0.0049). `16_decision_layer.py` reads
  `calibration_h{H}.json` and picks by measured ECE. **Do not hardcode a scorer.** That bug shipped
  once, and `run_all.py` then ran it at the wrong horizon.
- **Thresholds are horizon-specific and the scenario ranking is not horizon-robust.** At h3
  `capacity_matched` is dominated by `food_security_weighted`; at h6 it is the other way round. Any
  dominance claim must name the horizon.
- **The decision layer is pinned to h3**, for two reasons: the perishability window is short, and
  **80% of lots have a usable score at h3 against 64% at h6**, so h3 wins on recall *and* on food
  loss simultaneously.
- **The decision layer's metrics are a policy's performance on 52 plants**, not the model's on 578.
  The rule-based recall of 1.000 is a property of that narrow supply base; on the full panel at h3
  the Category 2 flag scores recall 0.915, precision 0.145.
- **"Exposure" is not an illness count.** It is pounds distributed uncooked from plants whose
  sampling later deteriorated. It was called "missed risk" until that name was judged to imply a
  claim the FSIS licence forbids.
- **The aminoglycoside heuristic overcalls badly.** Our gene→class map agrees with FSIS WGS calls on
  99.8–99.9% for beta-lactam, tetracycline, sulfonamide and phenicol, but only **62.3%** for
  aminoglycoside (918 FSIS-resistant against 3,310 carrying a gene). Every published MDR figure uses
  the FSIS WGS calls, not the heuristic, but a judge reading that table will ask, so the report
  must say so.
- **The Census API key is rejected** ("Invalid Key"; the confirmation email has a link that must be
  clicked). So `vulnerability_county.csv` is SVI alone, with no USDA food-access or ACS population
  layer. R6.1 asks for both; `FINDINGS.md` states the gap.
- **PowerShell, not bash.** Rushi works in PowerShell on Windows. Bash heredocs (`<<'EOF'`) fail
  there; a multi-line commit message goes in a file and `git commit -F file`.
- **Nothing is committed under `data/raw` or `data/processed`.** That is 62 MB of federal open data
  that belongs to FSIS. `.gitignore` handles it. Do not commit it.

---

## 9. Tooling

Developed with **Kiro** (AWS agentic IDE), signed in through IAM Identity Center. Kiro specs,
steering files and hooks in `.kiro/` are themselves graded artifacts, 15% of the score.

**Provenance, stated plainly:** Kiro did not generate the code in this repository. The `.kiro/`
artifacts are in Kiro's format and were loaded in Kiro, but they, `17_build_app_data.py`, and the
React application were written with Claude (Anthropic) between 2026-10-26 and 2026-10-28, by a team
decision to hand-build Phase 4 given the time remaining. The manual-change log at the end of
`.kiro/specs/onehealth-decision-support/tasks.md` lists every file with the date and reason. The
README and `app/README.md` say the same. Do not write anything that implies otherwise.

`.kiro/steering/project.md` is `inclusion: always` and carries the hard rules.

---

## 10. State of 1.6, which is mid-flight

`analysis/scripts/19_build_data_dictionary.py` exists in draft but **is not yet committed**. It
regenerates `data/DATA_DICTIONARY.md` across all 18 built tables, resolves FSIS descriptions through
the organism-prefix rename that `02_build_tables.py` applies (`sal_isolates.ampicillin_mic` is the
dictionary's `salmonella_ampicillin_mic`), and **refuses to invent a description**: an unknown
column is written out as UNDOCUMENTED and `--check` exits non-zero while any remain.

63 columns still need honest descriptions, concentrated in `cecal.parquet` (14) and
`establishments.parquet` (34). They are real FSIS columns whose text is not in
`data_dictionary_primary.csv` or `_secondary.csv`, so they have to be written from the source files
or flagged for a human. That is the next piece of work.
