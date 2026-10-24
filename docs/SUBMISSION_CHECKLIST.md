# Submission checklist

Taken verbatim from the Sens-D Submission Workspace on the NAFSI Hub, read 2026-10-24.

**How submission works:** you submit the **link to the GitHub repository** through the Submission
Workspace. The README must contain complete instructions for running every notebook and script.
Judges must be able to reproduce the work from those instructions alone.

## The six required items

- [ ] **1. Reproducible analysis notebooks and scripts.** All code for preprocessing, data
      integration, modeling, evaluation and **scenario analysis**. Running it must reproduce the
      results reported in the final report.
      *Status: pipeline complete and reproducible. Scenario analysis not yet built.*

- [ ] **2. Kiro development artifacts.** Kiro specs and/or prompt markdown files, steering files (or
      equivalent project guidance), and any hooks used for testing or documentation. **Disclose any
      substantial manual changes made to Kiro-generated code.**
      *Status: `.kiro/steering/project.md` written. Specs and hooks to follow as the app is built.*

- [ ] **3. Decision-support application.** A runnable web application with build and deployment
      instructions. NAFSI recommends React with GitHub Pages, for consistency with the prior NAFSI Hub
      application challenge.
      *Status: not started. Blocked on the challenge brief.*

- [ ] **4. Data dictionary and provenance file.** For each dataset: source, access date, licence,
      geographic coverage, time coverage, update frequency, transformations applied, known limitations.
      *Status: `data/DATA_DICTIONARY.md` and `data/PROVENANCE.md` complete for all current datasets.
      Any dataset added later must be appended to both.*

- [ ] **5. PDF report.** Methods, task outputs, responses to the challenge questions, model metrics,
      figures, decision scenarios, limitations, and a **team science statement**.
      *Status: outline in `report/OUTLINE.md`. Written by the team, not by AI.*

- [ ] **6. README and requirements files.** Clear setup instructions and every dependency needed to
      reproduce both the analysis and the application.
      *Status: `README.md` and `requirements.txt` cover the analysis. App dependencies to follow.*

## Deadline

**Monday 2026-11-02, 14:00 PT / 15:00 MT / 16:00 CT / 17:00 ET.**

> "Do not push any changes to your repository after the submission deadline. Any push made after the
> deadline will result in disqualification."

Treat the real cut-off as a few hours earlier. A last-minute fix that lands at 16:01 CT ends the entry.

The hub's team panel displays "Deadline: November 1, 2026", which contradicts both the challenge
Overview and the kickoff announcement. Both of those say November 2. Working to **November 1** removes
the risk either way.

## Open questions to resolve with the organisers

- **The challenge brief and the "challenge questions" have not been published.** Item 5 requires
  responses to them by name. Both fall tracks (Sens-D and Cultivate IQ) have empty
  `challenge_description` and `dataset_details` fields on the hub, where both spring challenges had a
  linked brief PDF and a dataset list. Asked 2026-10-24.
- Whether the fall rules place any restriction on AI assistance in the **written report**. The spring
  briefs asked teams not to use AI to write the report. The fall submission spec is silent on it while
  explicitly requiring Kiro artifacts for code.

## Events

- **Kiro tooling session: Monday 2026-10-26, 16:00 CT.** Personalised help using Kiro. Worth attending
  given Kiro artifacts are graded.
- Kickoff recording (contains requirements detail beyond the informational webinar):
  https://www.youtube.com/watch?v=U7CTaK4WCEM
- The USDA career panel on 2026-10-23 was **not recorded**.
