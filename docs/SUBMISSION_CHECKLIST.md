# Submission checklist

Six deliverables from the Sens-D Submission Workspace (read 2026-10-24), five required tasks and the
evaluation weights from the challenge brief (published 2026-10-26, extracted in
`docs/CHALLENGE_BRIEF.md`).

**How submission works:** submit the **GitHub repository link** through the Submission Workspace. The
README must let judges reproduce every result from its instructions alone.

---

## Deadline

**Monday 2026-11-02, 14:00 PT / 15:00 MT / 16:00 CT / 17:00 ET.** Confirmed by the challenge record's
`end_date` and by the Overview tab.

> "Do not push any changes to your repository after the submission deadline. Any push made after the
> deadline will result in disqualification."

The hub's team panel still displays "Deadline: November 1, 2026", contradicting both the Overview and
the challenge record. **Work to November 1.** That removes the risk whichever is authoritative, and a
fix landing at 16:01 CT ends the entry.

---

## The six deliverables

- [ ] **1. Reproducible analysis notebooks and scripts**: preprocessing, integration, modeling,
      evaluation and **scenario analysis**.
      *FSIS pipeline complete, validated at 99.75%, reproducing in about three minutes. NORS outcome
      layer added. Missing: climate, recalls, vulnerability, calibration, ablation, scenarios.*

- [ ] **2. Kiro artifacts**: specs, prompts, steering files, hooks. **Disclose substantial manual
      edits to Kiro-generated code.**
      *Steering written. Spec rewritten against the real brief at
      `.kiro/specs/onehealth-decision-support/`; the superseded `watchlist-app` spec is kept
      deliberately. Hooks not yet configured.*

- [ ] **3. Decision-support web application**: runnable, with build and deployment instructions.
      React recommended.
      *Not started. No longer blocked: fully specified, with the five required components named.*

- [ ] **4. Data dictionary and provenance**: per dataset: source, access date, licence, geographic
      and time coverage, update frequency, transformations, limitations, **and decision value**.
      *Complete for FSIS and NORS. Four datasets still to add.*

- [ ] **5. PDF report**: methods, task outputs, **answers to the ten report questions**, metrics,
      figures, scenarios, limitations, team science statement.
      *Outline only. Written by the team, not by AI.*

- [ ] **6. README and requirements**: setup and every dependency for analysis and application.
      *Covers the analysis. App dependencies to follow.*

---

## The five required tasks

- [ ] **T1 Define the system and data layer**: actor, decision, One Health system map, aligned
      datasets, data dictionary, provenance, decision statement.
      *Actor chosen (regional food bank, justified in the spec). Map and three datasets outstanding.*
- [ ] **T2 Build and validate a risk model**: transparent baseline, integrated model, time-aware
      validation, discrimination **and calibration**, uncertainty, **marginal value of added data**.
      *Baseline, integrated model, time-aware validation, bootstrap uncertainty and Brier scores done,
      with a gradient-boosting reliability table. Missing: reliability for the projection scorer, a
      reliability figure, and the leave-one-source-out ablation.*
- [ ] **T3 Convert predictions to decisions**: feasible actions, constraints, **food-security or
      equity objective**, comparison against a rule-based policy, **three or more scenarios**, human
      review for high-consequence actions.
      *Rule-based comparison exists. Everything else outstanding.*
- [ ] **T4 Build the app with Kiro**: current-risk view, alert queue, scenario builder,
      recommended-action panel, evidence panel with uncertainty.
      *Specified, not built.*
- [ ] **T5 Team science**: roles, two added datasets, ablation, a decision changed by another
      discipline, the next dataset or partner.
      *Outstanding. Capture the cross-discipline decision as it happens, not retrospectively.*

---

## Evaluation weights

| Criterion | Weight | Where we stand |
|---|---|---|
| Data science rigor and validation | 25% | strongest |
| Operational decision support | 25% | weakest, and worth the most alongside rigor |
| One Health and multi-source integration | 20% | three required sources still missing |
| Kiro implementation and usability | 15% | steering and spec in place, app not built |
| Team science, reproducibility, communication | 15% | reproducibility strong, team science untouched |

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

---

## Still open with the organizers

- **Whether the fall rules restrict AI assistance in the written report.** The spring briefs asked
  teams not to use AI to write the report; the fall materials are silent while explicitly requiring
  Kiro artifacts for code. We are treating the report as the team's own writing.
- `docs/CHALLENGE_BRIEF.md` is an **extracted summary**, not the organizers' verbatim text. Someone
  must check it against the Google Doc before the report is written.

## Events

- **Kiro tooling session: Monday 2026-10-26, 16:00 CT.** Attending.
- Kickoff recording, which may carry requirement detail not in the brief:
  https://www.youtube.com/watch?v=U7CTaK4WCEM
- The USDA career panel on 2026-10-23 was not recorded.
