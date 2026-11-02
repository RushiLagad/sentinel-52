# Submission checklist

Six deliverables from the SENS-D Submission Workspace (read 2026-10-24), five required tasks and the
evaluation weights from the challenge brief (published 2026-10-26, extracted in
`docs/CHALLENGE_BRIEF.md`). Status as of 2026-11-02, the submission day.

**How submission works:** submit the **GitHub repository link** through the Submission Workspace. The
README must let judges reproduce every result from its instructions alone.

---

## Deadline

**Monday 2026-11-02, 14:00 PT / 15:00 MT / 16:00 CT / 17:00 ET.** Confirmed by the challenge record's
`end_date` and by the Overview tab.

> "Do not push any changes to your repository after the submission deadline. Any push made after the
> deadline will result in disqualification."

The hub's team panel displayed "Deadline: November 1, 2026" for part of the challenge, contradicting
both the Overview and the challenge record. The team worked to the earlier date where it could and
submitted on the morning of November 2.

---

## The six deliverables

- [x] **1. Reproducible analysis notebooks and scripts**: `analysis/run_all.py` runs scripts 01 to
      20: FSIS pipeline validated against three official postings (99.75 percent), NORS burden,
      NOAA climate, FSIS recalls, SVI, synthetic inventory, model, calibration, two ablations,
      decision layer with four scenarios, figures, data dictionary. Reproduced on two machines.
- [x] **2. Kiro artifacts**: specs, steering and hooks under `.kiro/`. The manual-change log at the
      end of `.kiro/specs/onehealth-decision-support/tasks.md` states what Kiro generated (the
      Export CSV button and its test, 2026-11-01) and what was written by hand with Claude.
- [x] **3. Decision-support web application**: React, seven sections covering the five required
      views, 20 tests, four guardrails enforced in code, deployed to GitHub Pages on every push.
      Build and run instructions in `app/README.md`.
- [x] **4. Data dictionary and provenance**: `data/PROVENANCE.md` (every dataset: source, access
      date, licence, coverage, update frequency, transformations, limitations, decision value) and
      `data/DATA_DICTIONARY.md` (every column of every built table, regenerated on each run).
- [x] **5. PDF report**: `report/REPORT.pdf`, built from `report/REPORT.md`. Methods, the ten
      questions, metrics, seven figures, scenarios, limitations, team science statement, AI
      disclosure.
- [x] **6. README and requirements**: setup for analysis and app, manual data download with hash
      verification, a three-minute judge's path through the live app.

---

## The five required tasks

- [x] **T1 Define the system and data layer**: regional food bank as actor; decision statement in
      the README; One Health system map (`fig6`); five FSIS sources, CDC NORS, NOAA, FSIS recalls,
      CDC/ATSDR SVI; dictionary and provenance.
- [x] **T2 Build and validate a risk model**: binomial projection baseline, logistic and gradient
      boosting; time-aware split; AUROC and average precision with establishment-clustered
      bootstrap; reliability and ECE for both scorers at three horizons; leave-one-group-out
      ablation of FSIS features (05d) and the marginal value of the team-added layers (05e).
- [x] **T3 Convert predictions to decisions**: four actions with shelf-life and cooked-channel
      constraints; equity by SVI quartile; rule-based baseline; four scenarios; frontier; human
      acknowledgement with reversal evidence for every high-consequence call.
- [x] **T4 Build the app with Kiro**: current risk, alert queue, scenario builder, recommended
      actions, evidence with uncertainty, plus a receiving desk and equity view. Provenance of the
      code is stated, not implied.
- [x] **T5 Team science**: roles and dates in the manual-change log; two added datasets (four in
      practice); ablation of their effect; five decisions changed by another discipline recorded in
      Q9; next dataset named (a real food bank receiving log).

---

## Evaluation weights

| Criterion | Weight | Where we stand |
|---|---|---|
| Data science rigor and validation | 25% | strongest: validated rebuild, clustered intervals, calibration, two ablations, two-machine reproduction |
| Operational decision support | 25% | strong: a real decision, costed scenarios, human review, live app |
| One Health and multi-source integration | 20% | four domains with real data; the USDA food-access layer did not land (Census key) and is disclosed |
| Kiro implementation and usability | 15% | specs, steering and hooks complete; one Kiro-generated feature; the rest hand-built and disclosed |
| Team science, reproducibility, communication | 15% | strong: documented decisions, a teammate's branch merged, reproduction on two machines |

---

## Guardrails that are testable, not decorative

- Never label a food, establishment or shipment **safe** or **unsafe** on the model alone.
- Prototype only: not a regulatory determination, not an outbreak declaration, not a substitute for
  epidemiologic investigation.
- High-consequence actions need human review and a statement of what evidence would change them.
- Expose uncertainty, provenance and driving signals.
- Check whether recommendations disadvantage high-need communities, and report it either way.
- **Simulated inventory must be labelled simulated** everywhere it appears.
- No dataset under a redistribution restriction enters this repository.
- No FSIS-to-illness join at establishment level, ever.

All eight are enforced by `17_build_app_data.py --check` and the app's test suite, or by the
absence of the restricted files from the tree.

---

## Resolved with the organizers' materials

- **AI assistance in the written report.** The fall materials require Kiro artifacts for code and are
  silent on the report. The narrative was AI-drafted and team-edited, and the report's AI disclosure
  says so.
- `docs/CHALLENGE_BRIEF.md` is an extracted summary, not the organizers' verbatim text. Two team
  members read the report against the organizers' material before submission (task 5.7).

## Events

- Kiro tooling session, 2026-10-26, 16:00 CT: attended.
- Kickoff recording: https://www.youtube.com/watch?v=U7CTaK4WCEM
