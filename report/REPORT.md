# Sentinel-52: a receiving-desk decision tool for a regional food bank

**NAFSI Hub Student Data Challenge, Fall 2026, SENS-D track.**
Rushikesh Lagad (University of Arkansas), Sambhavi Patel (University of Arkansas), Naisargi Modha (Northeastern University).

> **DRAFT STATUS. Sections Q1, Q4, Q5, Q8 and Q10 below were drafted by Claude (Anthropic) on 2026-10-28
> from `report/OUTLINE.md`, `report/FINDINGS.md` and the analysis outputs, at the team's request, so
> that writing would start from complete, cited paragraphs rather than from notes. The team's own
> policy (`docs/SUBMISSION_CHECKLIST.md`) is that the report is the team's writing. Two ways to honour
> that: rewrite these sections in your own words before submission, or keep them and change the AI
> disclosure (Q10 and the README) to say the narrative was AI-drafted and team-edited. Do one or the
> other. Every number below traces to a named file and none was computed for this draft.**

Live application: https://rushilagad.github.io/sentinel-52/ · Repository: https://github.com/RushiLagad/sentinel-52

---

## Q1. The decision-maker and the decision horizon

The brief asks for one supply-chain actor and a decision that actor actually makes. We chose a regional food bank in Arkansas, and the choice was about the challenge question rather than convenience. The question asks how an actor can protect health while preserving food availability, supporting food security, and minimizing avoidable food loss. For a processor or a retailer those three are constraints on a safety decision. For a food bank they are the mission, and they collide with protecting health every day. Discard a pallet of chicken on a weak signal and people with no alternative go without; distribute it on a missed signal and the people harmed are the least able to absorb harm. For this actor the conflict the brief asks us to surface is the daily job, not a hypothetical.

The decision is taken per lot, inside the lot's perishability window: for each incoming or on-hand lot of FSIS-regulated poultry, distribute now, prioritize for immediate distribution, hold for review, or divert. The mechanism that makes this possible is ordinary. The USDA mark of inspection on every case carries the establishment number, so a pallet traces to the plant that produced it, and that plant has a public sampling history going back to fiscal year 2014.

Divert does not mean discard. A plant with a deteriorating sampling trajectory does not make its product inedible; it makes uncooked distribution the wrong channel for it. Diverting to a partner that cooks on site keeps the food in the system and applies a validated kill step. That is the actor-specific move that lets the health objective and the loss objective be traded against each other rather than simply opposed, and it is why the tool is a receiving-desk tool and not a recall simulator.

The forecast horizon is three months. Two reasons, one about the decision and one we did not anticipate. The decision is taken within days, so the nearest horizon is the relevant one. And coverage: 80 percent of lots have a usable score at the three-month horizon against 64 percent at six months, because the six-month test window ends earlier and more lots fall past the staleness limit. An unscored lot is distributed with the gap named, so coverage feeds directly into recall. Run at six months the conservative policy reaches recall 0.272 and destroys 62,042 meals; at three months it reaches 0.403 and destroys 30,529. Three months is better on both axes at once (`report/FINDINGS.md`, Finding 4).

The tool ranks what to look at first and puts a cost on each choice. It is not a regulatory determination, not an outbreak declaration, and not a statement that any food, lot or plant is safe or unsafe.

---

## Q4. The modeled outcome

The unit is a plant and product class, one of the five FSIS Salmonella performance standards, observed on the 52-week moving window FSIS itself uses. The outcome is entry into FSIS Category 3 within the forecast horizon: the point at which FSIS's own rating says a plant has exceeded its standard. We chose that outcome rather than a positivity rate because it is the status quo signal a food bank would otherwise act on, which makes the comparison to the baseline honest.

The category rebuild underneath this was validated before anything was modeled. Recomputing Category 1, 2, 3 and NA from the raw samples agrees with three official FSIS postings on 99.75 percent of 2,764 posted rows with zero false Category 3s (`analysis/outputs/category_validation.json`). The one rule FSIS does not document, how a borderline count rounds, was inferred empirically and is stated as such in the limitations.

Validation is time-aware. Training runs through September 2022; the test period begins in January 2024 and runs forward, so no window in the test set overlaps any window the models saw. At three months the test set holds 17,343 unit-months with 644 new Category 3 entries, a base rate of 3.71 percent (`analysis/outputs/early_warning_summary_h3.json`).

Three scorers were compared. The transparent baseline is a binomial projection: given the plant's current positive count and its sampling rate, the probability it crosses the Category 3 line within the horizon. Logistic regression and gradient boosting add sampling history, position against the standard, serotype detail, enumeration, the other pathogens FSIS tests, follow-up sampling, establishment profile, seasonality and product class. A leave-one-group-out ablation with establishment-clustered bootstrap intervals tested whether any of those additions carried signal (`analysis/outputs/t19_ablation_h6.csv`).

Which scorer the decision layer uses is chosen by measured calibration at the horizon it runs at, not by discrimination. A hold-or-divert decision acts on an absolute probability, so a score that ranks well but says 0.44 when the truth is 0.30 is the wrong score to act on. At three months the projection is far better calibrated than gradient boosting, expected calibration error 0.0056 against 0.0213, with the projection's top decile predicting 34.2 percent against 30.0 percent observed and gradient boosting's predicting 43.7 percent against 30.3 (`analysis/outputs/calibration_h3.json`). At six months the order reverses, 0.0092 against 0.0049. The decision layer reads the calibration file and picks, rather than carrying a hardcoded choice. Earlier in the project it did carry one, and the pipeline then ran it at the wrong horizon; that bug is why the choice is now data-driven.

---

## Q5. Performance against the baseline

The required rule-based baseline is the one a food bank would use today: treat anything from a Category 2 or Category 3 plant as suspect. On the full panel at three months that flag reaches recall 0.915 and precision 0.145 while flagging 23.5 percent of all units (`analysis/outputs/early_warning_summary_h3.json`). It is a good detector and a poor allocator.

Against it, at six months, the projection scores AUROC 0.917 and gradient boosting 0.925. The difference is real but small: the establishment-clustered bootstrap over 578 plants resampled whole gives a median gain of 0.008 AUROC with a 95 percent interval from 0.000 to 0.016, and a median gain in average precision of 0.003 with an interval from minus 0.036 to plus 0.041, which is not distinguishable from zero (`analysis/outputs/early_warning_summary_h6.json`). We report that as plainly as the gain, because the ablation explains it. Only three feature groups move AUROC beyond noise at six months: sampling history, the projection itself, and all of the additions taken together. Serotype detail, the other pathogens, follow-up sampling, establishment profile, seasonality and product class are each within noise (`t19_ablation_h6.csv`). The transparent baseline carries the signal.

Where the model earns its place is in allocation, not accuracy. A projection watch list the same size as the Category 2 list reaches recall 87.7 percent against the flag's 81.3 at equal precision; a list one tenth the size of the rated population reaches precision 41.5 percent at recall 66.0 (`analysis/outputs/watchlist_comparison_h6.json`). Lead time is usable: 86 percent of new Category 3 entries were on the top-10 percent list a month before they entered, and 62.6 percent three months before.

The three-month ablation verdicts are not reported because they are not stable. Two builds of the same data on two machines flipped `standard_position` between "carries signal" and "within noise", a consequence of 644 positives against 979 at six months and correspondingly wider intervals. The six-month ablation reproduces to the digit across machines, and the decision layer's outputs at three months reproduce to the digit as well. We quote what reproduces.

---

## Q10. What the tool can and can never claim, and what deployment would require

The tool can say which plants are on a deteriorating sampling trajectory, how far ahead that is visible, how well calibrated the number is, and what each policy for acting on it costs in shared units. Those claims rest on real public data and on results reproduced independently on two builds.

It can never say that any food, lot or plant is safe or unsafe. No output uses those words about anything, the application's test suite fails if one appears, and the only sentence in the whole system that contains them is the restriction that says we never use them. It can never link a plant to an illness. The FSIS data licence forbids using the sampling data to associate samples with outbreaks, and this project honours that by construction: every join between FSIS sampling and CDC NORS illness data is made at serotype and year, no code constructs an establishment-level link, the One Health system map draws that arrow crossed out with the reason on it, and the app data build fails if an establishment identifier appears beside a burden figure. It can never report a real poundage. A food bank's lot-level inventory is not public and we have none, so the inventory is generated by a seeded procedure, every row carries `is_synthetic = True`, and every pounds or meals figure in the application carries a SIMULATED mark that the build enforces. The ranking, the error rates and the direction of the equity effect do not depend on the simulation's scale; the absolute pounds depend on it entirely. And the quantity we call exposure, food distributed uncooked from plants whose sampling later deteriorated, is not a count of illnesses and must never be read as one. It was renamed from "missed risk" for exactly that reason.

Deployment would need five things this prototype does not have. Real inventory with lot-level provenance, under agreement with a food bank, which would turn every simulated figure into a measurement. A cooked-meal partner with a stated capacity, so that diversion is a real channel and discard is a measured overflow rather than a modelled one. The USDA food-access layer that requirement R6.1 asks for alongside SVI, which did not land because the Census API key was rejected, so equity is currently judged on county-level SVI alone. A review workflow in which acknowledging a high-consequence recommendation does something, with the evidence that would reverse it attached, where today it records only that a person read it. And FSIS data fresher than the quarterly posting cycle; the median score a lot is matched to is 19 days old, and a lot whose plant has not been sampled within 120 days is treated as unscored rather than as low risk.

Everything above is a prototype in the organizers' sense: not a regulatory determination, not an outbreak declaration, and not a substitute for epidemiologic investigation.

---

## Q2. The role of each core dataset
*To be written. Evidence and numbers in `report/OUTLINE.md`.*

## Q3. The added datasets and their impact
*To be written. Evidence and numbers in `report/OUTLINE.md`. Carries the 2.1 paragraph: the additions do not move the risk model, so they were used where they do matter, in the decision layer.*

## Q6. Which errors are costly
*To be written.*

## Q7. Where food safety and food security conflict
*To be written.*

## Q8. An end-to-end scenario

Three lots from the receiving desk, taken as they appear in `analysis/outputs/t23_lot_actions_h3.csv` under the conservative scenario. The plants, their sampling histories, categories and scores are real. The lots themselves, their weights, dates and destination counties, are simulated, and carry that mark in the application.

**The lot the tool was built for.** On 5 March 2026 a pallet of comminuted turkey arrives, 4,608 pounds, bound for Pulaski County. The mark of inspection gives establishment 8371, Prestage Foods. The desk shows the call in large type: send it to the cooked-meal channel. The reason is one sentence: the plant's projection is at or above the divert threshold. Behind it, the evidence. FSIS currently rates the plant Category 2. In the last 52 weeks, 8 of 60 routine samples were positive. The projection puts the probability of the plant entering Category 3 within three months at 0.79, and the score is five days old. Of plants scored at that level historically, about 30 percent did go on to Category 3. The lot has 124 days of shelf life, so there is no time pressure pushing the call either way. The desk states what the call costs: 4,608 pounds leave direct distribution to Pulaski County and go to a partner that cooks. It states the other choice: distribute now, which keeps the pounds in the pantry network and accepts the signal above. And it states what would reverse the call: the projection falling below 0.30, FSIS posting a Category 1 rating, or a clean 52-week window at the plant. Because divert is high-consequence, a dialog blocks until a person has read all of that and acknowledges it. Acknowledging changes nothing in the world. It records that a person read the call, and the next lot needing a decision comes up.

**The lot that shows what a hold costs.** On 3 February 2026 a pallet of chicken parts arrives from Case Farms, establishment 750, 2,621 pounds for Faulkner County. The plant is also Category 2, with 6 of 52 samples positive, but the projection is 0.08, far below the divert line and just above the conservative scenario's hold line of 0.05. The call is hold for review. The lot has nine days of shelf life. Review takes seven days, and getting a released lot through the pantry network takes three. Nine is less than ten. Under this policy the hold destroys the food, and the desk says so in the record: lost, shelf life exhausted by the review hold. Nobody discarded anything on purpose. This is the mechanism by which a conservative policy, which looks free when you count only what it catches, destroys 30,529 meals on this supply base, and it is why the frontier in Q6 is not convex. A weak signal on a fresh lot is a decision between distributing it and losing it; holding it is not actually available.

**The same plant, eight months earlier.** On 12 July 2025 a smaller pallet of comminuted turkey arrived from the same Prestage plant, 1,454 pounds for Yell County. The most recent score for that plant and product was 350 days old, far past the 120-day staleness limit, so the desk treated the lot as unscored and distributed it with the gap named: no recent sampling for this plant and product. It did not treat an old score as a current one, and it did not treat the absence of a score as low risk. It said what it did not know. By March 2026 the same plant had 8 positives in 60 and a projection of 0.79, and the tool caught it. Whether it would have caught it earlier with fresher sampling is exactly the question the limitations section is honest about.

Those three lots are the project. A strong signal with time to act becomes a diversion that keeps the food in the system. A weak signal on a perishable lot is a choice the tool makes visible rather than a hold it pretends is free. And a missing score is reported as missing. Every number in them is in the application, and a reader can find each lot by its identifier on the receiving desk.

## Q9. The effect of team science on the work
*To be written from tasks 5.1 and 5.2.*

## Limitations
*To be written from the list in `report/OUTLINE.md`.*

## Team science statement
*To be written.*

## AI assistance disclosure
*To be written. Must state, consistently with the manual-change log in `.kiro/specs/onehealth-decision-support/tasks.md`: Kiro did not generate code in this repository; the `.kiro/` artifacts are in its format and were loaded in it. Claude (Anthropic) was used for the analysis pipeline, scripts 09 to 19, the specs, steering and hooks, `17_build_app_data.py`, the React UI and its tests, and, if these drafted sections are kept, the narrative of Q1, Q4, Q5 and Q10. The team reviewed, ran and is responsible for all of it.*
