# Requirements: Sentinel-52 watch-list application

## Introduction

Sentinel-52 is the decision-support web application required by item 3 of the SENS-D submission.

It supports one decision, stated plainly: **given a limited number of establishment-months you can
inspect, which ones should they be?** FSIS and processors cannot sample everywhere. The posted
Salmonella categories tell you who is failing *now*. This application tells you who is on track to
fail *next*, and what you give up by watching a shorter list.

The analysis behind it is already built and validated in `analysis/`. The application does not
re-derive anything; it reads pre-computed outputs and makes them usable by someone who has to
choose where to send people this month.

### Who uses it

- **A regulator or policy analyst** deciding where verification sampling should concentrate.
- **A processor's food-safety lead** asking whether their own plants are drifting toward Category 3.
- **A judge** who needs to see, in a few minutes, that the claims in the report are real.

### What it deliberately is not

It is not a contamination predictor and must never be presented as one. It reorders attention over
establishments using their own recent sampling history. Every screen must make that limit legible
rather than hide it.

---

## Requirement 1: Ranked watch list

**User story.** As a regulator with finite inspection capacity, I want establishments ranked by their
projected risk of entering Category 3, so that I can direct sampling at the units most likely to fail
next rather than the ones that failed last.

### Acceptance criteria

1. WHEN the application loads THE SYSTEM SHALL display a list of currently rated establishment and
   product-class units ordered by descending risk score.
2. THE SYSTEM SHALL show, for each unit: establishment number, establishment name, state, HACCP size
   class, product class, current posted category, trailing 52-week positive count and sample count,
   the standard's allowed positives for that window, and the risk score.
3. WHEN a unit has been on the watch list in previous months THE SYSTEM SHALL display how many
   consecutive months it has appeared.
4. THE SYSTEM SHALL allow filtering by state, HACCP size class, product class, and current category.
5. THE SYSTEM SHALL allow text search by establishment name or number.
6. WHERE a unit is currently Category 3 THE SYSTEM SHALL mark it as already failing rather than
   as a prediction, because it is not a forecast for that unit.
7. THE SYSTEM SHALL state the sample collection window the posted categories come from, verbatim
   from the source data, on the same screen as the list.

---

## Requirement 2: Sampling-budget scenario

**User story.** As an analyst who can only follow up on so many units a month, I want to see what a
shorter or longer list costs me, so that I can defend the size of the list I actually use.

This is the scenario analysis required by submission items 1 and 5. It is the core of the application,
not a secondary screen.

### Acceptance criteria

1. THE SYSTEM SHALL provide a control that sets the watch-list size as a share of currently rated
   units, spanning at least 5 percent through 30 percent.
2. WHEN the list size changes THE SYSTEM SHALL update the displayed precision, recall, the implied
   number of units per month, and the watch list itself.
3. THE SYSTEM SHALL display the three evaluated strategies side by side at their measured operating
   points, drawn from `watchlist_comparison_h6.json`:
   - current Category 2 flag: 23.6 percent of units, 21.9 percent precision, 81.3 percent recall
   - risk projection at the same list size: 23.6 percent of units, 23.6 percent precision, 87.7 percent recall
   - risk projection, top 10 percent: 10.1 percent of units, 41.5 percent precision, 66.0 percent recall
4. THE SYSTEM SHALL express each operating point in units per month as well as percentages, using the
   measured medians: 641 rated units, 154 on the Category 2 flag, 65 on the top 10 percent list.
5. THE SYSTEM SHALL make the comparison against the Category 2 flag explicit, because that flag is
   the status quo and beating it is the claim being made.
6. IF a displayed operating point is interpolated rather than measured THE SYSTEM SHALL label it as
   interpolated.

---

## Requirement 3: Lead-time evidence

**User story.** As someone deciding whether this is worth adopting, I want to know how far in advance
the list flags a failure, because a warning that arrives a week early is worthless operationally.

### Acceptance criteria

1. THE SYSTEM SHALL display the share of new Category 3 entries that appeared on each list at least
   k months before onset, for k from 1 through 6, from `watchlist_comparison_h6.json`.
2. THE SYSTEM SHALL state the denominator: 257 new Category 3 entries across 160 distinct
   establishments, with onset windows ending between 2024-07-27 and 2026-06-27.
3. THE SYSTEM SHALL disclose that 28 of those entries arrived from an unrated state and therefore
   could not have been ranked in advance by any method that needs sampling history.

---

## Requirement 4: Establishment detail

**User story.** As a user who has found a unit on the list, I want its own history, so that I can see
whether the ranking is driven by a real trend or by one bad window.

### Acceptance criteria

1. WHEN a user selects a unit THE SYSTEM SHALL display its sampling history over the available
   fiscal years: samples taken, positives, and posted category by window.
2. THE SYSTEM SHALL show where the unit sits relative to the standard for its product class.
3. WHERE serotype information exists for that unit's positives THE SYSTEM SHALL display it, and
   WHERE it does not THE SYSTEM SHALL say so rather than leaving the panel blank.
4. THE SYSTEM SHALL display the share of positives that carry a serotype nationally, so a user
   reads an empty serotype panel as normal rather than as a defect.

---

## Requirement 5: Why this matters

**User story.** As a judge or a reader new to the problem, I want to understand in one screen why
proactive targeting is worth building, so that the rest of the application has a reason to exist.

### Acceptance criteria

1. THE SYSTEM SHALL display the FSIS FY2022-2026 Salmonella indicator against its target, showing
   the recomputed baseline of 4.20 percent, the FY2026 value of 5.78 percent, and the 3.80 percent
   target, and SHALL state that the indicator moved away from the target rather than toward it.
2. THE SYSTEM SHALL show the concentration of Category 3 by establishment size: 6.7 percent of large
   plants, 18.2 percent of small, 25.4 percent of very small.
3. THE SYSTEM SHALL show the Infantis shift in serotyped chicken isolates, from 3.5 percent to 36.1
   percent, alongside its multidrug-resistance share of 86.2 percent across 1,996 isolates, compared
   with 3.3 percent across 1,259 Kentucky isolates.
4. THE SYSTEM SHALL present these as surveillance observations, not as causal claims.

---

## Requirement 6: Traceability

**User story.** As a judge checking the work, I want every number on screen to be traceable to a file
in the repository, so that I can verify rather than trust.

### Acceptance criteria

1. THE SYSTEM SHALL source all displayed figures from files under `analysis/outputs/`, never from
   values hard-coded in component source.
2. THE SYSTEM SHALL display the generation timestamp and the source filename for each data panel.
3. THE SYSTEM SHALL provide a link to `data/PROVENANCE.md` and `data/DATA_DICTIONARY.md`.
4. THE SYSTEM SHALL disclose the two known method caveats on a visible page: that the FSIS
   categorisation rounding rule is inferred empirically rather than documented, and that the category
   rebuild matches 2,757 of 2,764 posted rows, which is 99.75 percent, with zero false Category 3.
5. THE SYSTEM SHALL carry the FSIS use restriction that the data must not be used to link
   establishments to illness outbreaks.

---

## Requirement 7: Static deployment

**User story.** As a judge, I want to open a URL and have it work, without installing anything or
running a server.

### Acceptance criteria

1. THE SYSTEM SHALL build to static assets servable from GitHub Pages.
2. THE SYSTEM SHALL NOT require a backend, a database, or any network call at runtime.
3. THE SYSTEM SHALL function when served from a repository subpath, not only from a domain root.
4. IF a data file fails to load THE SYSTEM SHALL display which file is missing rather than an
   empty screen.
5. THE SYSTEM SHALL remain usable at a viewport width of 390 pixels.

---

## Requirement 8: Readability

**User story.** As any user, I want the charts to be readable, including in a colourblind-safe sense
and in dark mode, because a surveillance tool that misleads at a glance is worse than a table.

### Acceptance criteria

1. THE SYSTEM SHALL never encode category or risk by colour alone; a label or shape SHALL accompany it.
2. THE SYSTEM SHALL provide a table view of every chart.
3. THE SYSTEM SHALL use a single y-axis per chart.
4. THE SYSTEM SHALL render legibly in both light and dark mode.

---

## Requirement 9: Burden weighting

**User story.** As a regulator allocating inspection effort, I want the watch list to account for
which serotypes actually put people in hospital, so that I am not spending capacity on a serotype
that is common in the supply but rarely makes anyone ill.

This requirement exists because the two rankings disagree. In FSIS chicken sampling, Kentucky is
16.6 percent of serotyped isolates and carries zero outbreak-associated hospitalizations in NORS over
2014 to 2023. Infantis is 36.1 percent and carries 31. Enteritidis is 22.8 percent and carries 184.
Prevalence in the supply is not a proxy for harm, so a tool that ranks on positivity alone
misallocates attention by construction.

### Acceptance criteria

1. THE SYSTEM SHALL display, for chicken, each serotype's share of serotyped FSIS isolates alongside
   its NORS outbreak count and hospitalizations, from `t17_chicken_prevalence_vs_burden.csv`.
2. THE SYSTEM SHALL offer a burden-weighted ordering of the watch list as an alternative to the
   unweighted projection, and SHALL allow the user to switch between them and see which units move.
3. WHEN burden weighting is active THE SYSTEM SHALL state that the weight derives from
   outbreak-associated illness only, which is a small and biased subset of all salmonellosis.
4. THE SYSTEM SHALL display, for every serotype burden figure, the share of that figure contributed
   by its single largest outbreak, from `pct_hosp_from_largest_row`.
5. WHERE a serotype's burden is dominated by one outbreak, meaning that share exceeds 80 percent,
   THE SYSTEM SHALL mark it as resting on a single event rather than on a pattern.
6. THE SYSTEM SHALL display the policy comparison: that the 2024 proposed framework serotypes
   capture 65.7 percent of chicken-attributed hospitalizations but 6.8 percent of turkey-attributed
   hospitalizations, and that the highest-burden turkey serotype, Reading, appears on neither the
   framework list nor the FSIS indicator.
7. THE SYSTEM SHALL state that 32.3 percent of Salmonella foodborne hospitalizations carry no IFSAC
   food category at all, so poultry-attributed burden is a floor rather than an estimate.
8. THE SYSTEM SHALL NOT present any establishment alongside any outbreak. All joins are at serotype
   and year, as the FSIS data licence requires.

---

> **SUPERSEDED 2026-10-26.** Written before the challenge brief was published, from the track title
> alone. It aimed the tool at a regulator allocating inspection capacity; the brief asks for a
> supply-chain actor. Replaced by `.kiro/specs/onehealth-decision-support/`.
>
> Kept rather than deleted because the brief asks how the work evolved, and a tidied history would
> misrepresent that. The model, validation and evidence requirements here carried over almost intact.
