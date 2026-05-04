# AsPredicted Pre-registration
# Can I Still Code? Longitudinal Study of AI Tool Use and Python Coding Skill

**Platform:** https://aspredicted.org/
**PI:** Andy Woods, Royal Holloway, University of London (andy.woods@rhul.ac.uk)
**Co-I:** Alex Reppel, Royal Holloway, University of London
**Ethics approval:** Royal Holloway University of London Research Ethics Committee (approved 20 April 2026)

---

## 1. Have any data been collected for this study already?

No. The platform is undergoing internal testing only. Participant data collection begins after this registration is timestamped. Researcher/staff accounts are excluded from analysis by design.

---

## 2. What is the main question being asked or hypothesis being tested?

Does self-reported AI-assisted coding predict changes in Python skill over time, within the same participant?

**H1 (accuracy, primary):** Higher within-person AI use in the previous session will be associated with lower challenge accuracy (binary pass/fail) in the current session.

**H2 (speed, primary):** Higher within-person AI use in the previous session will be associated with slower completion time in the current session.

**H3 (dose-response, secondary):** The H1/H2 associations will be larger among participants with higher overall AI use, tested as a lagged-AI × mean-AI interaction.

The study is observational; all hypotheses are stated as associations, not causal claims.

---

## 3. Describe the key dependent variable(s) and how they will be measured.

**Primary outcomes:** (1) Challenge accuracy -- binary pass/fail on automated test cases run client-side (Pyodide/WebAssembly); (2) active completion time -- seconds from first edit to final submission, excluding idle periods >60 s. No raw code is stored; only derived values are transmitted.

**Primary AI exposure:** Per-session self-reported % of code AI-generated in the past month (0--100), person-mean centred; lagged (previous-session) value is the key predictor.

**Secondary outcomes (exploratory):** Code complexity metrics (cyclomatic complexity, Halstead effort, LOC, nesting depth), efficiency ratio (participant vs. reference execution time), run attempts.

---

## 4. How many and which conditions will participants be assigned to?

Observational study; no random assignment. Participants vary naturally in AI use. Primary time variable: months since baseline session (calendar time). Primary predictor: per-session % AI-generated code, person-mean centred.

---

## 5. Specify exactly which analyses you will conduct to examine the main question/hypothesis.

All analyses in R (`lme4`). Unit of analysis: challenge attempt (sessions nested in participants; challenge identity cross-classified).

H1 -- logistic mixed model (binomial):

```
accuracy_pass ~ challenge_difficulty + challenge_type
              + months_since_baseline
              + ai_past_month_pwc_lag1 + ai_past_month_mean
              + (1 + months_since_baseline | participant_id)
              + (1 | session_id) + (1 | challenge_id)
```

`ai_past_month_pwc_lag1`: previous session's % AI-generated code, person-mean centred (primary exposure). `ai_past_month_mean`: participant mean (between-person). If non-convergent, random slope dropped first, then `(1|challenge_id)` moved to sensitivity.

H2: same structure, outcome = `log(active_completion_time_seconds)`, LMM.

Alpha = 0.05, two-tailed. Effects reported as standardised coefficients / odds ratios as appropriate, 95% CI (parametric bootstrap where feasible). Session-level sensitivity: binomial mixed model (passed/attempted). Minimum: 100 participants with ≥3 sessions.

---

## 6. Describe exactly how outliers will be defined and handled, and your precise rules for excluding observations.

Excluded: staff/researcher sessions; challenge attempts with completion time >3 h; participants with only one session or no prior Python experience. Challenge attempts with completion time <10 s are retained in primary analyses but excluded in sensitivity analyses. Completion time log-transformed; no further removal. Listwise deletion on missing outcome, exposure, time, difficulty, or challenge identity; no imputation.

---

## 7. How many observations will be collected, or what will determine sample size?

Target: 200+ participants completing ≥3 sessions (target 400+), open-access, 12-month minimum. No definitive power analysis is possible because key variance components and retention rates are unknown. With 200 participants × 4 sessions × 12 challenges, the expected dataset would contain ~9,600 challenge attempts, expected to provide useful precision for estimating small within-person associations (Maas & Hox, 2005). Primary analysis will be conducted at 12 months if at least 100 participants have contributed ≥3 sessions; otherwise deferred until this minimum is reached.

---

## 8. Anything else you would like to pre-register?

**Secondary analyses:** S1 (H3: lagged-AI × mean-AI interaction); S2 (complexity LMMs); S3 (efficiency ratio LMM); S4 (run attempts, negative binomial GLMM); S5 (tertile subgroups); S6 (AI-free practice moderator); S7 (thematic analysis of free-text, reported separately).

**Challenge set:** 12 challenges per session (2 bespoke screening tier 0 + 10 MBPP/HumanEval tiers 1--5), randomised without repetition within participant. Participants instructed not to use AI or external help; compliance is honour-system self-report.

**Open data:** Pseudonymised dataset released CC-BY 4.0 after 12-month embargo; scripts on GitHub. Deviations reported transparently.

---

## 9. Type of study

Observational longitudinal study (no intervention or random assignment).

---

## 11. Data source

**Other:** Purpose-built citizen-science web platform (canistillcode.org).
