# Requirements: Sentinel-52 One Health decision support

## Introduction

This spec replaces `.kiro/specs/watchlist-app/`, which was written before the challenge brief was
published and aimed the tool at a regulator. The brief asks for a **supply-chain actor**. See
`docs/CHALLENGE_BRIEF.md`.

### The decision-maker: a regional food bank

**This is a team decision and the one thing in this spec most worth overruling.** The brief offers
processor, distributor or logistics operator, retailer, and regional food bank. This spec picks the
food bank, for a reason that is about the challenge question rather than convenience.

The question asks how an actor can protect health *while preserving food availability, supporting
food security, and minimizing avoidable food loss*. For a processor those last three are side
constraints. For a food bank they are the mission, and they are in direct, daily tension with the
first. Discard a pallet of chicken on a weak signal and people who have no alternative go without.
Distribute it on a missed signal and the people harmed are the ones least able to absorb harm. The
conflict the brief asks us to surface is not hypothetical here; it is the job.

It also makes the One Health integration real rather than decorative. A food bank sits where food
production (FSIS), human illness (NORS), environmental conditions (NOAA) and population vulnerability
(SVI, food access) actually meet.

The mechanism is concrete: USDA marks of inspection carry the establishment number, so an incoming
pallet of poultry can be traced to the plant that produced it, and that plant has a sampling history.

### Decision statement

> For each incoming or on-hand lot of FSIS-regulated poultry, the food bank must decide within its
> perishability window whether to **distribute now**, **prioritize for immediate distribution**,
> **hold for review**, or **divert**, given the producing establishment's near-term risk, the
> nutritional need of the communities it serves, and the loss created by discarding edible food.

### What this is not

Not a regulatory determination. Not an outbreak declaration. Not a safety verdict on any food,
establishment or shipment. It reorders attention and surfaces evidence for a human decision.

---

## Requirement 1: Current-risk view

*Brief Task 4, component 1.*

**User story.** As a food-bank operations lead, I want to see the risk standing of every establishment
whose product I currently hold, so that I know where to look before anything goes wrong.

### Acceptance criteria

1. THE SYSTEM SHALL display each establishment supplying current inventory with its near-term
   elevated-risk score, its current FSIS category, and its trailing 52-week positives against the
   standard's allowance.
2. THE SYSTEM SHALL display the serotype profile of that establishment's recent positives where one
   exists, and SHALL say so explicitly where it does not.
3. THE SYSTEM SHALL show the lots held from each establishment, with quantity and days remaining in
   the perishability window.
4. THE SYSTEM SHALL NOT render any establishment, lot or food as "safe" or "unsafe".
5. THE SYSTEM SHALL state the posted sampling window the FSIS categories derive from, verbatim.
6. WHERE an establishment has no recent sampling THE SYSTEM SHALL mark it as unrated rather than
   low-risk, because absence of sampling is not absence of risk.

---

## Requirement 2: Alert queue

*Brief Task 4, component 2.*

**User story.** As an operations lead with a finite number of decisions I can make carefully today, I
want a ranked queue of what changed, so that I spend attention where it moved.

### Acceptance criteria

1. THE SYSTEM SHALL present a queue ordered by projected risk, restricted to establishments whose
   status changed or whose risk crossed a threshold since the previous period.
2. THE SYSTEM SHALL state, for each alert, what drove it: a rise in positivity, a serotype of higher
   burden, a recall or public-health alert, or a climate signal.
3. THE SYSTEM SHALL display an FSIS recall or public health alert affecting a held lot at the top of
   the queue regardless of model score, because a recall is a fact and not a prediction.
4. THE SYSTEM SHALL let the user mark an alert reviewed, with the action taken recorded.
5. THE SYSTEM SHALL show how many units per period the current threshold implies, so the queue length
   is a staffing decision the user makes knowingly.

---

## Requirement 3: Scenario builder

*Brief Task 4 component 3, and Task 3's requirement of at least three scenarios.*

**User story.** As a planner, I want to see what a policy costs before I adopt it, in food distributed
and food discarded as well as in risk caught.

### Acceptance criteria

1. THE SYSTEM SHALL let the user vary: the risk threshold for holding a lot, the review capacity per
   period, and the weight given to the food-security objective.
2. WHEN any control changes THE SYSTEM SHALL update precision, recall, pounds held, pounds discarded,
   pounds distributed, and the share of distribution reaching high-vulnerability communities.
3. THE SYSTEM SHALL ship with at least three named, pre-built scenarios:
   - **Conservative**: hold on weak signals. High recall, high food loss.
   - **Capacity-matched**: queue length matched to actual review capacity.
   - **Food-security weighted**: distribution to high-need areas protected, holds concentrated
     elsewhere, with the risk this accepts stated plainly.
4. THE SYSTEM SHALL compare every scenario against the **rule-based policy**: hold anything from a
   Category 2 or 3 establishment. That is the status quo and the baseline to beat.
5. THE SYSTEM SHALL display the trade-off as a frontier, not a single recommended operating point,
   because the choice is a value judgement and not an optimisation.

---

## Requirement 4: Recommended-action panel

*Brief Task 4, component 4.*

**User story.** As the person who has to act, I want a specific recommended action and the reason for
it, not a risk score I have to interpret.

### Acceptance criteria

1. THE SYSTEM SHALL recommend exactly one of: distribute now, prioritize for immediate distribution,
   hold for review, or divert.
2. THE SYSTEM SHALL state the reason in one sentence naming the driving signal.
3. THE SYSTEM SHALL state what the recommendation costs: pounds affected and the communities served
   by that inventory.
4. WHERE the recommendation is hold or divert THE SYSTEM SHALL mark it **high-consequence** and
   SHALL require explicit human confirmation, and SHALL name the evidence that would change it.
5. THE SYSTEM SHALL never auto-execute an action.
6. THE SYSTEM SHALL offer the opposite action with its own cost, so the user sees the choice rather
   than a verdict.

---

## Requirement 5: Evidence panel with uncertainty

*Brief Task 4 component 5, and the guardrail on exposing uncertainty and provenance.*

**User story.** As someone accountable for the decision, I want to see what the recommendation rests
on and how firm it is.

### Acceptance criteria

1. THE SYSTEM SHALL show the establishment's sampling history, the signals contributing to the score,
   and the direction of each.
2. THE SYSTEM SHALL display the score with an interval from establishment-clustered bootstrap, never
   as a bare point estimate.
3. THE SYSTEM SHALL display model **calibration** for the risk band the establishment falls in: of
   units scored at this level historically, the share that actually went on to elevated risk.
4. THE SYSTEM SHALL name the source file and generation date of every figure shown.
5. WHERE a serotype burden figure is used THE SYSTEM SHALL display the share of that burden coming
   from a single outbreak, and SHALL flag anything above 80 percent as resting on one event.
6. THE SYSTEM SHALL link to `data/PROVENANCE.md` and `data/DATA_DICTIONARY.md`.
7. THE SYSTEM SHALL state the FSIS restriction: these data cannot establish causal links to illness,
   and nothing here attributes an illness to an establishment.

---

## Requirement 6: Food-security and equity objective

*Brief Task 3, and the guardrail on high-need communities. This is the requirement most likely to be
skipped and it carries weight in two of the five criteria.*

**User story.** As a food bank, I need to know whether my risk policy is quietly taking food away from
the communities that can least replace it.

### Acceptance criteria

1. THE SYSTEM SHALL join service areas to a population-vulnerability measure (CDC/ATSDR SVI) and a
   food-access measure (USDA food-access data).
2. THE SYSTEM SHALL report, for any scenario, the distribution reaching high-vulnerability areas
   against low-vulnerability areas.
3. THE SYSTEM SHALL run an explicit **disparity check**: whether holds and diversions fall
   disproportionately on high-need service areas, with the result stated whichever way it comes out.
4. WHERE a policy reduces supply to high-need areas more than to others THE SYSTEM SHALL surface that
   as a finding on the scenario screen, not in a footnote.
5. THE SYSTEM SHALL NOT optimise the disparity away silently. The trade-off is shown and the human
   chooses.

---

## Requirement 7: Avoidable food loss

*Brief challenge question, explicit.*

### Acceptance criteria

1. THE SYSTEM SHALL track pounds held, diverted and discarded under each policy.
2. THE SYSTEM SHALL report avoidable loss: food discarded from establishments that did not go on to
   elevated risk, which is the cost of a false alarm measured in meals.
3. THE SYSTEM SHALL express false-alarm and missed-risk costs in the same units wherever possible, so
   the two error types can be weighed against each other rather than discussed abstractly.

---

## Requirement 8: Model, validation and data value

*Brief Task 2.*

### Acceptance criteria

1. THE SYSTEM SHALL use the **transparent binomial projection** as the default scorer, with the
   integrated model available and both intervals shown when switching.
2. THE SYSTEM SHALL report discrimination (AUROC, average precision) **and calibration** (reliability
   curve and Brier score) for whichever scorer is displayed. Brier and a gradient-boosting reliability
   table already exist in `05_early_warning_baseline.py`; the projection scorer's reliability table and
   a reliability figure do not.
3. THE SYSTEM SHALL use time-aware validation: training strictly before the test window.
4. THE SYSTEM SHALL report an **ablation** giving the marginal contribution of each added source
   (climate, serotype burden, vulnerability, recalls) over the FSIS-only baseline.
5. WHERE an added source does not improve performance THE SYSTEM SHALL report that honestly and the
   source SHALL remain in the ablation table rather than being quietly dropped.

---

## Requirement 9: Reproducibility and deployment

### Acceptance criteria

1. THE SYSTEM SHALL read only pre-computed files produced by the pipeline; no runtime API calls.
2. THE SYSTEM SHALL build to static assets servable from GitHub Pages at a repository subpath.
3. THE SYSTEM SHALL name the missing file on a failed load rather than rendering blank.
4. THE SYSTEM SHALL remain usable at 390 pixels wide.
5. No dataset under a redistribution restriction SHALL enter this repository. NORS comes from the
   public CDC endpoint; the organizers' emailed extract is not used by any script.

---

## Requirement 10: Readability

### Acceptance criteria

1. Risk and category SHALL never be encoded by colour alone.
2. Every chart SHALL have a table view.
3. One y-axis per chart.
4. Light and dark mode both legible, palette validated rather than eyeballed.
