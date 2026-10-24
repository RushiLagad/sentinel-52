# Report outline

The PDF report is a required deliverable and is **written by the team**. This file is a skeleton of
the sections the submission spec requires, not draft text.

Required coverage, from the Submission Workspace: *"methods, task outputs, responses to the challenge
questions, model metrics, figures, decision scenarios, limitations, and a team science statement."*

---

## 1. Problem framing
What question the tool answers and for whom. Tie explicitly to the challenge questions once published.

## 2. Data
Datasets used and why. Point to `data/PROVENANCE.md` rather than repeating it. State the FSIS use
restriction and how the work respects it.

## 3. Methods
- Building the sample and isolate tables from the raw FSIS JSON
- Rebuilding FSIS Category 1/2/3/NA, and the one empirical rounding rule that is inferred rather than
  documented
- The hazard layer: serotype, sequence-based resistance calls, enumeration
- Early-warning task definition: unit, horizon, time split, and why the split is set where it is

## 4. Task outputs
Answers to the challenge questions, each one labelled.

## 5. Model metrics
Baselines and models side by side, with establishment-clustered intervals. Report where the model does
**not** beat the baseline as plainly as where it does.

## 6. Figures
Each figure carries its source table. Every number traceable to `analysis/outputs/key_numbers.json`.

## 7. Decision scenarios
Worked examples of the tool changing a decision. The candidate framing: a plant is told how many more
positives it can absorb in its next n samples before it changes category, and what its current
positives actually are.

## 8. Limitations
At minimum: the inferred categorisation rounding rule; the October 2026 establishment snapshot applied
to earlier years; enumeration missing after 2026-04-28 and absent for turkey carcasses; sampling
composition changes across years; the 3 to 6 month publication lag; and the fact that predicting which
plants fail is largely arithmetic rather than a modelling achievement.

## 9. Team science statement
How the three of us divided and integrated the work across two institutions.

## 10. AI assistance disclosure
Kiro's role, Claude's role in the earlier pipeline, and any substantial manual changes to generated
code.
