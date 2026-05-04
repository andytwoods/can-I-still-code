# AsPredicted Pre-registration
# Longitudinal Assessment of the Relationship Between AI-Assisted Coding Practices and Python Coding Skill

**Platform:** https://aspredicted.org/
**PI:** Andy Woods, Royal Holloway, University of London (andy.woods@rhul.ac.uk)
**Co-I:** Alex Reppel, Royal Holloway, University of London
**Ethics approval:** Royal Holloway University of London Research Ethics Committee (approved 20 April 2026)

---

## 1. Have any data been collected for this study already?

No. The platform is operational and undergoing internal testing by the research team only. No participant data have been collected prior to this registration. Data collection will begin after this pre-registration is timestamped. Any researcher/staff accounts are excluded from analysis by design.

---

## 2. What is the main question being asked or hypothesis being tested?

**Primary question:** Does self-reported use of AI-assisted coding tools predict changes in Python coding skill over time, within the same participant?

**H1 (accuracy):** Higher within-person AI tool use will be associated with lower challenge accuracy (proportion of automated test cases passed) at subsequent sessions, after controlling for session number, challenge difficulty, and participant-level covariates.

**H2 (speed):** Higher within-person AI tool use will be associated with slower active challenge completion time at subsequent sessions, after controlling for the same covariates.

**H3 (dose-response):** Any negative association between AI tool use and skill outcomes will be larger in magnitude among participants with higher cumulative AI use across the study period.

The study is observational and longitudinal. Participants self-select into levels of AI tool use; there is no experimental manipulation. All hypotheses are therefore stated as associations, not causal claims.

---

## 3. Describe the key dependent variable(s) and how they will be measured.

**Primary outcome variables (analysed at challenge level, aggregated to session level for some models -- see Section 5):**

- **Challenge accuracy:** Whether the participant's submitted code passed all automated test cases for a given challenge (binary: pass/fail). Tests are run client-side using Pyodide (Python via WebAssembly); only the pass/fail result is transmitted to the server. Aggregated to session level as the proportion of challenges fully passed (range 0--1).

- **Active completion time:** Time in seconds from when the participant first edited the code to final submission, excluding browser-tab idle periods exceeding 60 seconds. Measured client-side using `performance.now()`.

**Secondary outcome variables (per challenge, exploratory):**

- **Code complexity metrics:** Computed entirely client-side from the submitted code using Python's `ast` module. Metrics include: cyclomatic complexity, Halstead effort, lines of code (non-blank), maximum nesting depth, count of list/dict/set comprehensions, generator expressions, ternary expressions, unique identifier count, and function definition count. Only the resulting numeric values are transmitted to the server; raw code is never sent or stored.

- **Efficiency ratio:** Ratio of the participant's median code execution time to the reference solution's median execution time, both timed in the same Pyodide session after tests complete. A value of 1.0 means equivalent performance; values above 1.0 indicate slower execution than the reference.

- **Run attempts:** Number of times a participant ran/tested their code before final submission.

**Self-report variables collected per challenge (post-challenge survey):**

- Perceived challenge difficulty (subjective self-report, 5-point Likert: Very easy / Easy / Moderate / Difficult / Very difficult -- distinct from the objective difficulty tier, which runs 0--5)
- Confidence in solution (5-point: Not at all confident / Not confident / Neutral / Confident / Very confident)
- Whether they looked anything up (No; Checked docs; Searched web; Used AI tool; Mix of the above)
- Perceived effect of AI use on this challenge (Harder / No difference / Unsure / Easier / I don't regularly use AI)

**Self-report variables collected per session (post-session survey):**

- Percentage of code written in the past month that was AI-generated (numeric, 0–100). Directly usable as a continuous predictor in the LMM; participants are asked to give a rough estimate.
- Overall coding confidence right now (5-point scale)
- Perceived session difficulty (5-point scale)
- Trust in AI-generated code (5-point scale)
- Percentage of AI-generated code they review (numeric, 0--100)
- Frequency of deliberate AI-free coding practice (5-point scale)
- Percentage of coding time kept deliberately AI-free (numeric, 0--100)
- Free-text comments about the session (optional)
- Free-text description of steps taken to protect coding skills (optional)

**Baseline covariates (profile survey, completed once):** Age range, gender identity, country of residence, years coding experience, Python proficiency (self-rated 1--5), primary programming role, employment sector, primary AI tool used, frequency of AI-assisted coding, proportion of code that is AI-generated, prior LLM coding tool use, and habitual first response when stuck on a problem.

---

## 4. How many and which conditions will participants be assigned to?

This is an observational study. Participants are not randomly assigned to conditions.

The primary time-varying predictor is **session-level AI use**, operationalised as the proportion of challenges in the session for which the participant reported using an AI tool (post-challenge question: "Did you look anything up?" coded as 1 if response is `used_ai` or `multiple`, 0 otherwise). This is computed per session and will vary naturally within participants across sessions.

Absolute AI use level at baseline is captured once via the profile survey ("roughly what proportion of your final code is AI-generated?"). A per-session numeric question ("roughly what percentage of the code you wrote in the past month was AI-generated?", 0--100) creates a time series of AI exposure directly usable as a continuous predictor in the LMM.

Participants will be grouped post-hoc for descriptive purposes only (not used in primary models) based on their mean AI use across all sessions: consistently low, consistently high, increasing over time, decreasing over time.

---

## 5. Specify exactly which analyses you will conduct to examine the main question/hypothesis.

All analyses will be conducted in R. Analysis scripts will be published alongside the dataset on GitHub.

**Unit of analysis:** The primary analysis uses the challenge attempt as the unit of analysis, with sessions nested within participants. A session-level sensitivity analysis (averaging accuracy and completion time across challenges per session) will also be reported.

**Primary models (H1 and H2):**

Three-level linear mixed-effects models (LMMs) fitted with the `lme4` package. Observations are challenge attempts (Level 1) nested in sessions (Level 2) nested in participants (Level 3).

Model structure for H1 (accuracy):

```
logit(accuracy_adj) ~ challenge_difficulty + challenge_type
                    + prior_attempts_this_challenge
                    + session_number
                    + ai_use_session_pwc + ai_use_session_pwc_lag1
                    + (1 | participant_id/session_id)
                    + (1 | challenge_id)
```

Where:
- `accuracy_adj` is binary pass/fail, proportion-adjusted using the Smithson-Verkuilen transformation to handle boundary values before logit: `(y * (n-1) + 0.5) / n` where n is the number of test cases. Where a challenge has only one test case (binary outcome), a logistic mixed model (GLMM with binomial family) will be substituted.
- `challenge_difficulty` is the challenge difficulty tier (0--5), included as a fixed covariate to control for variation in challenge difficulty across sessions.
- `challenge_type` is a binary indicator distinguishing benchmark challenges (MBPP/HumanEval, tiers 1--5) from screening challenges (bespoke, tier 0), as these are qualitatively different instruments.
- `session_number` is the within-person session index (1, 2, 3 ...) capturing general time-on-study trends.
- `ai_use_session_pwc` is the session-level AI use proportion (proportion of challenges in the session coded as AI-assisted), person-mean centred to isolate within-person effects. The person mean is retained as a separate between-person predictor.
- `ai_use_session_pwc_lag1` is the AI use proportion from the immediately preceding session (lagged predictor), person-mean centred.
- `(1 | participant_id/session_id)` captures random intercepts at participant and session level.
- `(1 | challenge_id)` captures the cross-classified random intercept for each individual challenge, accounting for idiosyncratic challenge difficulty beyond what the tier and type covariates capture (e.g. unusually worded problems, challenges that are well-known in developer culture). This gives a cross-classified rather than purely nested random effects structure.
- If the full model fails to converge, random slopes for `session_number` at the participant level will be dropped first; if still non-convergent, `(1 | challenge_id)` will be moved to a sensitivity analysis. Any such deviation will be reported.

Model for H2 uses `log(active_completion_time_seconds)` as the outcome with the same predictor structure.

**Significance threshold:** alpha = 0.05 two-tailed. H1 and H2 are co-primary; no correction for multiple comparisons is applied across them, and this will be stated explicitly in any resulting publication. Effect sizes reported as standardised beta coefficients with 95% confidence intervals (parametric bootstrap, 1,000 iterations).

**Minimum data requirement for analysis:** Models will only be fitted if at least 100 participants have contributed three or more sessions. If this threshold is not met at the planned 12-month analysis point, analysis will be deferred.

---

## 6. Describe exactly how outliers will be defined and handled, and your precise rules for excluding observations.

**Session-level exclusions:**

- Sessions completed by researcher/staff accounts will be excluded from all analyses.
- Sessions where fewer than 4 challenges were attempted will be excluded (incomplete sessions).
- Sessions where total active time is less than 3 minutes (likely abandoned or non-genuine) will be excluded.

**Challenge-level exclusions:**

- Challenge attempts where active completion time is below 10 seconds (implausible; likely copy-paste of a pre-written solution) will be flagged. These will be retained in primary analyses but excluded in a sensitivity analysis.
- Challenge attempts where active completion time exceeds 3 hours will be treated as data errors and excluded.
- Challenge attempts where the efficiency ratio exceeds 1,000 (indicating pathological code, e.g. an infinite loop that timed out) will have the efficiency ratio set to missing; the attempt itself will be retained.

**Outlier handling for continuous outcomes:**

- Completion time will be log-transformed prior to analysis to reduce skew; no further outlier removal will be applied after transformation.
- Cyclomatic complexity and Halstead effort values above the 99th percentile will be Winsorised to the 99th percentile value before any secondary analyses involving these variables.

**Participant-level exclusions:**

- Participants who complete only one session cannot contribute within-person estimates and will be excluded from primary LMMs but included in descriptive statistics.
- Participants who report in the profile survey that they have no prior Python experience will be excluded (inclusion criterion violation).

All exclusion decisions will be made and documented before the analysis dataset is finalised. A CONSORT-style participant flow diagram will be included in any publication.

---

## 7. How many observations will be collected, or what will determine sample size?

**Target sample:** Minimum 200 participants completing at least three sessions; target 400+. No upper limit. The study is citizen-science and open-access.

**Study duration:** Minimum 12 months from the date recruitment opens. Sessions are separated by a minimum of 28 days; each participant can contribute at most approximately 13 sessions over 12 months.

**Power analysis:** A formal power analysis for three-level LMMs is not tractable without prior estimates of the ICC and effect size in this domain. Based on simulation studies for repeated-measures designs with ICC of 0.3--0.5 (Maas & Hox, 2005), 200 participants contributing an average of 4 sessions and 10 challenges per session (N ≈ 8,000 observations) provides approximately 80% power to detect a standardised within-person effect of beta = 0.10 at alpha = 0.05. This estimate is conservative given the multilevel structure and is treated as a guide only. The study will recruit as many participants as feasible within the time window.

**Stopping rule:** Primary quantitative analysis will be conducted at 12 months regardless of sample size, subject to the minimum-data caveat in Section 5. The platform will remain open beyond 12 months if resources permit.

---

## 8. Anything else you would like to pre-register?

**Secondary analyses:**

- **S1 (H3, dose-response):** Cumulative mean AI use (across all sessions per participant) will be added as a between-person moderator in the primary models and interacted with `session_number` to test whether trajectories differ by overall AI use level.

- **S2 (code complexity trajectory):** Separate LMMs with `cyclomatic_complexity` and `lines_of_code` as outcomes, using the same predictor structure as the primary models, to test whether coding style changes over time and whether AI use predicts those changes.

- **S3 (efficiency ratio trajectory):** LMM with `log(efficiency_ratio)` as the outcome to test whether code execution efficiency relative to reference solutions changes over time and with AI use.

- **S4 (run attempts):** LMM with number of run attempts before submission as the outcome.

- **S5 (subgroup):** Primary models re-run separately in the top and bottom tertile of cumulative AI use to assess whether patterns differ qualitatively.

- **S6 (protective behaviours moderation):** The percentage of coding time kept deliberately AI-free (post-session item) will be added as a moderator to test whether deliberate AI-free practice buffers against any negative AI use effect.

- **S7 (qualitative strand):** Exit survey free-text responses and optional semi-structured interview transcripts will be analysed using thematic analysis (Braun & Clarke, 2006) to explore participants' own accounts of perceived skill changes. Reported separately; used to contextualise quantitative findings.

**Challenge set:**

Participants complete challenges from two sources, which are analysed separately where appropriate: (a) published benchmark challenges (MBPP, HumanEval) used without modification to allow cross-study comparisons, at difficulty tiers 1--5; (b) bespoke screening challenges at difficulty tier 0. Session composition: 2 level-0 screening + 3 level-1 + 3 level-2 + 2 level-3 + 1 level-4 + 1 level-5 = 12 challenges per session. Assignment within tiers is randomised without replacement within a participant's history; each challenge is presented to a given participant at most once across the study.

**Open data release:**

The fully pseudonymised dataset will be released publicly (CC-BY 4.0) after a 12-month embargo from study close, subject to a pre-release identifiability review of any free-text fields. Analysis scripts will be released simultaneously on GitHub.

**Deviations:**

Any deviations from this pre-registration will be reported transparently in the methods section of any resulting publication, with justification.

---

## 9. Type of study

Observational longitudinal study (no intervention or random assignment).
