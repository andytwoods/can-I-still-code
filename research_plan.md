# Research Plan: Does Vibe Coding Degrade Coding Skill?

**Study title:** Longitudinal Assessment of the Relationship Between AI-Assisted Coding Practices and Python Coding Skill

**Lead researcher:** Andy Woods, Royal Holloway, University of London

**Document status:** Pre-registration draft (target: OSF pre-registration before data collection opens)

**Last updated:** 2026-02-19

---

## 1. Research Questions

1. **RQ1 (primary):** Does the proportion of coding time spent on AI-assisted ("vibe") coding predict a steeper decline in Python coding skill over time?
2. **RQ2:** Does vibe coding predict slower challenge completion times over time, independently of accuracy?
3. **RQ3:** Is the effect of vibe coding on skill change moderated by challenge difficulty tier — specifically, are everyday fluency skills (Tiers 1–2) more susceptible to degradation than algorithmic skills (Tiers 4–5)?
4. **RQ4:** Does total coding time (hours per week) buffer or amplify the effect of vibe coding on skill change?
5. **RQ5 (exploratory):** Do participants' subjective assessments of whether tasks have become harder since starting vibe coding correlate with their objective performance trajectories?
6. **RQ6 (qualitative):** How do participants explain changes (or non-changes) in their own coding skill, and what role do they attribute to vibe coding, codebase complexity, tool diversity, and other contextual factors?

---

## 2. Hypotheses

All hypotheses are directional and pre-registered. The key causal claim is that vibe coding displaces deliberate Python practice, reducing the retrieval strength of manual coding skills over time (cf. memory reconsolidation, desirable difficulties literature).

### Primary hypotheses

**H1 (core):** Participants who report a higher vibe-coding percentage will show a steeper decline in challenge accuracy over time (as measured by `tests_passed / tests_total`), after controlling for baseline ability, challenge difficulty, and total coding hours.

**H1b:** The passive reliance index (`vibe_intensity × (1 − review_thoroughness)`) will predict steeper accuracy decline more strongly than vibe-coding intensity alone, because cognitive disengagement from AI-generated code — not mere AI use — is the proximal cause of skill degradation.

**H2:** Participants who report a higher vibe-coding percentage will show a steeper increase in challenge completion time over time (as measured by `log(active_time_seconds)`), after the same controls.

### Secondary hypotheses

**H3:** The negative effect of vibe coding on accuracy over time (H1) will be larger for Tier 1–2 challenges than for Tier 3–5 challenges. Rationale: AI tools most thoroughly replace basic syntax and boilerplate recall; higher-tier problems require algorithmic reasoning that AI augments rather than replaces entirely.

> **Power caveat:** With ascending difficulty ordering and expected session dropout at challenge 4–6, the majority of attempts will be Tier 1–2 and Tier 3+ data will be sparse. H3 may be underpowered or untestable unless session design is adjusted (see §15 gap). If Tier 3–5 data are insufficient, H3 is downgraded to exploratory.

**H4:** Higher coding hours per week will attenuate (moderate) the negative effect of vibe coding on skill trajectory. Rationale: participants who code many hours may maintain manual practice volume even when a high proportion is vibe coded.

**H5:** Participants who report that tasks have become harder since starting vibe coding (post-challenge Q2 ratings) will show objectively steeper performance declines than those who report no difference.

### Null-result definition

A null result on H1 is defined as a 95% credible interval for the `vibe_coding_pct × months_since_baseline` interaction coefficient that contains zero and whose upper bound is below the minimum effect size of interest (MESI; see §9.2). A null result would suggest that vibe coding does not measurably impair the type of coding skill assessed here within the study timeframe.

---

## 3. Study Design

| Property | Value |
|----------|-------|
| Design | Observational longitudinal cohort study |
| Study type | Citizen science / open-participation |
| Population | Adults with existing Python coding experience |
| Recruitment | Open (social media, developer communities, university networks) |
| Time horizon | Minimum 12 months of data collection; analysis after ≥12 months |
| Session cadence | Maximum one session per 28 days; no minimum frequency. Minimum 2 sessions expected; mode ~6 sessions over the study period. |
| Session structure | 1–10 Python coding challenges per session; participant-controlled |
| Blinding | Participants are not told specific hypotheses beyond "we are studying AI coding and skill" |

This is a **purely observational study** — there is no random assignment to vibe-coding conditions. Causal inference is therefore limited; the study can establish longitudinal associations and is powered to detect moderation, but cannot rule out all confounds. See §11 (Limitations) for full discussion.

---

## 4. Variables

### 4.1 Primary Dependent Variable

| Variable | Operationalisation | Data field(s) | Notes |
|----------|--------------------|---------------|-------|
| **Accuracy** | Proportion of test cases passed per challenge attempt | `ChallengeAttempt.tests_passed / ChallengeAttempt.tests_total` | Bounded [0, 1]; use beta regression or treat as continuous with logit transform |

### 4.2 Secondary Dependent Variables

| Variable | Operationalisation | Data field(s) | Notes |
|----------|--------------------|---------------|-------|
| **Completion speed** | Active time per challenge | `log(ChallengeAttempt.active_time_seconds)` | Log-transform to handle right skew; exclude attempts flagged with `technical_issues = True` |
| **Composite score** | Weighted combination of accuracy and normalised speed | Derived at analysis time | Exploratory; weights to be pre-specified in analysis script |
| **Completion rate** | Proportion of session challenges attempted (not skipped) | `ChallengeAttempt.skipped` | Session-level outcome |

### 4.3 Primary Independent Variables

Two complementary measures of vibe-coding behaviour are collected per session. Together they yield a **passive reliance index** (see derived variable below) that more precisely captures the construct of interest than either measure alone.

| Variable | Question wording | Data field(s) | Time-varying? |
|----------|-----------------|---------------|---------------|
| **Vibe-coding intensity** | *"What percentage of your coding time is currently AI-assisted (i.e. AI generates most of the code, you guide and review)?"* 0–100% slider | `SurveyResponse` post-session | Yes |
| **AI code review thoroughness** | *"Of the code AI generates for you, roughly what percentage do you check over carefully?"* 0–100% slider | `SurveyResponse` post-session | Yes |
| **Passive reliance index** (derived) | `vibe_intensity × (1 − review_thoroughness / 100)` — high when using AI heavily *and* rarely checking its output | Computed at analysis time | Yes |

**Rationale for the review question:** a participant who generates 80% of their code with AI but checks every line carefully still engages cognitively with the code and may not experience skill degradation. A participant who generates 50% with AI and never checks it is more cognitively disengaged. The passive reliance index captures this distinction. It also removes the need to anchor the vibe-coding slider precisely — the review question grounds interpretation behaviourally. Primary model uses `vibe_coding_pct` alone (pre-registered); passive reliance index is a pre-registered secondary predictor (H1b).

### 4.4 Time Variable

| Variable | Operationalisation | Data field(s) |
|----------|--------------------|---------------|
| **Months since baseline** | Continuous; months elapsed between a participant's first completed session and the current session | Derived: `(CodeSession.completed_at − participant's first CodeSession.completed_at).days / 30.44` |

### 4.5 Pre-specified Covariates

| Variable | Rationale | Data field(s) | Time-varying? |
|----------|-----------|---------------|---------------|
| Challenge difficulty tier | Performance differs systematically by tier | `Challenge.difficulty` (Tier 1–5) | No (per challenge) |
| Hours coding per week | Total practice volume confounds vibe-coding effect | `SurveyResponse` post-session | Yes |
| Years Python experience | Baseline proficiency | `SurveyResponse` profile Q8 | No |
| LeetCode familiarity | Challenge-type familiarity inflates early scores | `SurveyResponse` profile Q14–16 | No |
| Device type | Typing fluency on phone/tablet may depress performance | `CodeSession.device_type` | Per-session |
| Distraction-free environment | Noisy sessions introduce variance | `CodeSession.distraction_free` | Per-session |
| Think-aloud active | Dual-task cost may slow performance | `ChallengeAttempt.think_aloud_active` | Per-attempt |
| Technical issues | Unreliable timing data | `ChallengeAttempt.technical_issues` | Per-attempt |

### 4.6 Exploratory Variables (not pre-registered for primary model)

- Time of day / day of week (derivable from `started_at` timestamps)
- Industry and role (`SurveyResponse` profile Q10–11)
- AI tools used (`SurveyResponse` profile Q18)
- Duration of vibe-coding experience (`SurveyResponse` profile Q19)
- Paste ratio (`ChallengeAttempt.paste_total_chars / len(submitted_code)`) as cheating covariate
- Retrospective skill change self-report (`SurveyResponse` profile Q21)

---

## 5. Primary Statistical Model

### 5.1 Specification

Frequentist multilevel regression fitted with `lme4` + `lmerTest` (R); p-values via Satterthwaite df approximation. `brms` retained as a pre-specified robustness check.

```r
lmerTest::lmer(
  accuracy_logit ~ vibe_coding_pct_c * time_unit
                 + review_thoroughness_c * time_unit   # passive reliance components
                 + hours_per_week
                 + difficulty_tier
                 + leetcode_familiarity
                 + device_type
                 + distraction_free
                 + (1 + time_unit || participant_id)   # || avoids singular fits
                 + (1 | challenge_id),
  data    = dat,
  control = lmerControl(optimizer = "bobyqa")
)
```

- **Random intercept + slope for participant (`||`):** decoupled (zero-correlation) parameterisation used to avoid singular fits with participants who have few sessions; the correlation can be added in the brms robustness check.
- **Random intercept for challenge:** captures item-level difficulty beyond the fixed tier rating.
- **Key interaction:** `vibe_coding_pct_c × time_unit` (H1); `review_thoroughness_c × time_unit` enters as a secondary term enabling the passive reliance index to be decomposed.
- **Time-varying predictors** (`vibe_coding_pct`, `review_thoroughness`, `hours_per_week`) use the value reported at the session containing each attempt.
- **Predictors are centred** (suffix `_c`) to aid convergence and make the intercept interpretable as average-participant, average-session accuracy.
- **`time_unit`** is months since baseline scaled to 3-month units (1 unit = one quarter).

### 5.2 Secondary Models

**S1 — Speed model:** same structure with `log(active_time_seconds)` as the outcome. Attempts with `active_time_seconds < 10` or `> 3600` excluded as implausible.

**S2 — Passive reliance model:** replaces the two separate vibe-coding terms with the derived passive reliance index (`vibe_pct × (1 − review_thoroughness)`), testing H1b.

**S3 — Tier moderation model:** extends the primary model with `vibe_coding_pct_c × time_unit × difficulty_tier_low_binary` (Tier 1–2 vs. Tier 3–5), testing H3. Treated as exploratory pending sufficient Tier 3+ data.

**S4 — Cross-source tier validation:** after ~3 months of data, compute the average pass rate per tier per source (Exercism, APPS, custom). If pass rates within a tier are comparable across sources, the human-assigned tier mapping is confirmed. If a source's tier diverges notably, re-map that source's challenges to an adjacent tier for future imports (documented in the challenge codebook). No IRT required — within-study pass rates are the empirical check, aggregated at the tier-source level (~50 attempts per cell needed, not per individual challenge).

**S5 — brms robustness check:** primary model re-fitted with `brms` using weakly informative priors (`Normal(0, 0.5)` for fixed effects; `Normal(0, 0.5)` truncated > 0 for SDs; `LKJ(2)` for correlations). Reported if results materially differ from the `lmerTest` primary.

---

## 6. Qualitative Component

The quantitative data captures *whether* skill changes; qualitative data captures *why* — the contextual factors, attributions, and lived experiences that numbers cannot. The coding buddy insight that prompted this section is illustrative: "I do a lot of varying things lately so it is impossible to be good at one tool + huge codebases I have to deal with — it is impossible to keep everything in my head." This points to an alternative explanation for apparent skill decline (cognitive load from tool/codebase diversity) that the quantitative model cannot fully disentangle.

### 6.1 Exit Survey

Presented to participants when they choose to leave the study (or at the 12-month mark). Free-text responses. Delivered via the unified question system (`context = "exit"`). All questions are optional.

| # | Question | Purpose |
|---|----------|---------|
| 1 | *Looking back, do you feel your Python coding skill has changed since you joined this study? If so, how?* | Subjective trajectory; check against objective data |
| 2 | *What do you think is the main reason for any change (or lack of change) you noticed?* | Attribution — vibe coding, practice, role change, etc. |
| 3 | *Has the complexity or variety of your work changed during the study (e.g. larger codebases, more tools, new languages)?* | Tests the "impossible to keep everything in my head" alternative explanation |
| 4 | *How has your relationship with AI coding tools changed over the course of the study?* | Trajectory of adoption/reliance |
| 5 | *Is there anything about your experience of the study you'd like us to know?* | Open feedback; surfaces unexpected themes |

Exit survey responses are analysed thematically (Braun & Clarke reflexive thematic analysis) as a standalone qualitative strand and used to contextualise and interrogate the quantitative findings.

### 6.2 Follow-Up Contact Permission

At the end of the exit survey (and optionally during the study on the profile page), participants are asked:

> *"Would you be willing to be contacted about future research related to this study (e.g. a follow-up survey or interview)?"*  Yes / No

- Stored as an `OptionalConsentRecord` with `consent_type = "future_contact"`.
- **Email address is not re-collected** — the participant's account email is used, and only if they have this consent active.
- Withdrawn participants or those who have requested data deletion are excluded from any contact list.

### 6.3 Interview Sub-Study

A purposive sample of willing participants (drawn from those who gave follow-up contact permission, §6.2) is invited for a semi-structured interview after the main data collection period.

**Sampling strategy:** maximum variation across:
- Vibe-coding intensity (low / medium / high)
- Objective skill trajectory (improving / stable / declining)
- Role and experience level

**Interview focus:**
- Their experience of skill change and what they attribute it to
- How they use AI tools in practice (what tasks, what proportion, how they verify AI output)
- Whether contextual factors (codebase size, tool switching, role change) feel more explanatory than AI use per se
- Their views on the study findings (member-checking component)

**Target N:** 15–20 interviews (theoretical saturation expected; reassess after 10).

**Analysis:** reflexive thematic analysis (Braun & Clarke). Reported as a qualitative supplement section in the same paper, using a convergent mixed-methods design (Creswell & Plano Clark, 2018); strands integrated at the interpretation stage.

**Ethics note:** interviews require a separate ethics amendment or are covered under the initial application if pre-declared. Declare in the ethics application. Interviews are recorded and transcribed (with consent); recordings deleted after transcription.

---

## 7. Inclusion and Exclusion Criteria

### 6.1 Participant-level inclusion

- Must have completed ≥ 2 sessions (to have a baseline and at least one follow-up).
- Must have answered the vibe-coding percentage question in ≥ 2 sessions.
- Must have given valid consent and not withdrawn before analysis.

### 6.2 Participant-level exclusion

- Staff / superuser accounts.
- Participants with `withdrawn_at` or `deletion_requested_at` set.
- Participants with evidence of systematic result fabrication (see §7.3).

### 6.3 Attempt-level exclusion (pre-specified sensitivity analysis)

The **primary analysis** uses all valid attempts. A **sensitivity analysis** re-runs the model excluding:

- Attempts where `paste_ratio > 0.8` AND the attempt is correct.
- Attempts with `active_time_seconds` below the 5th percentile for that challenge.
- Attempts with `technical_issues = True`.
- Sessions completed on phone or tablet (device-type sensitivity check).
- Sessions where `distraction_free = "no"`.

If results are materially different between primary and sensitivity analyses, this is reported as a key finding requiring discussion.

---

## 8. Power and Sample Size

### 7.1 Targets

| Target | Value | Justification |
|--------|-------|---------------|
| Minimum participants | 200 | Provides adequate variance in vibe-coding intensity (expected bimodal distribution) |
| Minimum sessions per participant | 2 | Baseline + at least one follow-up; sufficient for a change score |
| Expected sessions per participant | ~6 (mode) | Minimum 2, most participants expected to complete ~6 over the study period (~one every 1–2 months) |
| Study duration | 12 months | Minimum time for detectable skill change if effect exists |
| Expected total challenge attempts | ~6,000–18,000 | ~5 attempts per session × 6 sessions (expected mode) × 200 participants; upper bound assumes higher engagement and retention |
| Expected Tier 3–5 attempts | Low — sparse | With ascending difficulty ordering, participants who stop at challenge 4–6 will rarely reach Tier 3 and almost never Tier 4–5 (see §11 limitation) |

### 7.2 Minimum Effect Size of Interest (MESI)

Based on prior literature on skill decay (spacing effects, desirable difficulties), we consider a meaningful effect to be:

- **Accuracy:** a change of ≥ 5 percentage points per 6 months at the highest vibe-coding intensity (100%) relative to zero vibe-coding.
- **Speed:** a change of ≥ 15% in `active_time_seconds` per 6 months under the same contrast.

Effects smaller than these are considered practically insignificant for the claims being made, even if statistically credible.

### 7.3 Simulation-Based Power Analysis

Before launch: run simulation-based power analysis using `brms` or `simr`:

1. Simulate datasets under the MESI (§8.2) with the expected data structure (unbalanced, varying N sessions per participant).
2. Fit the primary model to each simulated dataset.
3. Calculate the proportion of simulations where the 95% CI for the key interaction excludes zero.
4. Target ≥ 80% power; adjust recruitment targets if needed.

Results of the power simulation to be documented in `analysis/power_simulation.Rmd` and appended to this document before pre-registration.

---

## 9. Analysis Timeline

| Milestone | When |
|-----------|------|
| Power simulation complete | Before recruitment opens |
| OSF pre-registration submitted | Before first participant completes first session |
| Cross-source tier validation | ~3 months post-launch (compare pass rates per tier per source; re-map outlier challenges if needed) |
| Interim descriptive analysis | 6 months post-launch (N, retention, covariate distributions) |
| Primary analysis | After ≥ 12 months of data AND ≥ 200 participants with ≥ 3 sessions |
| Sensitivity analyses | Immediately after primary analysis |
| Exploratory analyses | After pre-registered analyses are finalised and locked |
| Dataset embargo lifted | 12 months after first completed session |
| Paper submission target | Within 6 months of primary analysis |

---

## 10. Planned Paper Structure

Mapping research questions and hypotheses to paper sections:

### Introduction
- Background: rapid adoption of AI coding assistants; vibe coding as an emerging practice
- Theoretical framing: skill decay from disuse (cognitive science); desirable difficulties; retrieval practice
- Gap: no longitudinal empirical data on the relationship between AI coding assistance and manual coding skill
- Research questions (§1) and directional hypotheses (§2)

### Method
- Participants and recruitment
- Study design (§3)
- Measures: challenges (difficulty tiers, sources, cross-source tier validation), survey instruments (all SurveyQuestion items used)
- Procedure: session flow, timing, think-aloud (if activated)
- Statistical analysis plan (§5) and pre-registration details

### Results
- Descriptive statistics: sample demographics, vibe-coding distribution, retention, session counts
- Primary model: H1 and H2 (accuracy and speed trajectories × vibe-coding)
- Secondary models: H3 (tier moderation), H4 (hours-per-week moderation)
- Sensitivity analyses
- Exploratory: H5 (subjective vs. objective skill change)

### Discussion
- Interpretation of key interaction (or null result)
- Practical implications: should developers be concerned? What mitigates the effect?
- Limitations (§11)
- Future directions (§12)

---

## 11. Limitations

These are pre-acknowledged to prevent post-hoc rationalisation in the paper:

| Limitation | Nature | Mitigation |
|------------|--------|------------|
| **No causal identification** | Observational design; vibe-coding % is self-selected, not randomly assigned | Discuss direction-of-causality problem explicitly; use lagged predictors in sensitivity analysis (session N−1 vibe-coding predicting session N performance) |
| **Self-report vibe-coding measure** | Participants may not accurately estimate their vibe-coding percentage; socially desirable responding | Include retrospective Q (profile Q21) to check for consistency; report test-retest reliability of vibe-coding % across sessions |
| **Reverse causation** | Participants who experience skill degradation may increase vibe-coding use as a result (not a cause) | Cannot fully rule out; discuss theoretically; lagged predictor sensitivity analysis helps |
| **Attrition bias** | Dropout may be non-random — participants who notice skill loss may drop out, or may be more motivated to continue | Report retention by baseline vibe-coding group; test whether dropouts differ from completers on baseline characteristics |
| **Challenge practice effects** | Doing coding challenges monthly, even with no repeats, is itself a form of deliberate practice that may offset skill decay | Include time-on-study as a covariate in sensitivity analysis; compare early-joining vs. late-joining cohorts |
| **Sample bias** | Participants who enrol are intrinsically motivated, curious about their own skill trajectories, and likely more reflective about AI use than typical developers | Report recruitment channel distribution; note in paper that results may not generalise to less-engaged developers |
| **English-language challenges** | Non-native English speakers may be disadvantaged on description comprehension, inflating difficulty ratings | Include language fluency covariate (profile Q4); run sensitivity analysis excluding participants who report finding English challenging |
| **Vibe-coding definition ambiguity** | "AI generates most of the code, you guide and review" — participants may interpret this differently | Provide a concrete example in the question help text; acknowledge measurement error in the paper |
| **Short study window** | 12 months may be insufficient to detect gradual skill decay if the effect accrues over years | Report effect at 6 and 12 months separately; acknowledge that longer follow-up is needed |
| **Challenge pool exhaustion for long-term participants** | After ~20 sessions, participants have seen all challenges | Report N participants who approached exhaustion; note this limits the study to approximately 20 months per participant |
| **Sparse Tier 3–5 data** | Challenges are presented in ascending difficulty order; participants who stop at challenge 4–6 complete only Tier 1–2. Tier 3+ attempts will be rare, weakening H3 and the cross-source tier validation for higher-tier items | Report actual Tier 3–5 attempt counts before running S3 and S4; if sparse, downgrade H3 to exploratory and acknowledge limited generalisability to harder challenges |
| **Codebase complexity / tool diversity confound** | Skill decline may be driven not by vibe coding per se but by working on larger, more complex codebases with more diverse tools — making it cognitively impossible to stay fluent in any one area regardless of AI use. The quantitative model cannot disentangle this from vibe coding | Include exit survey Q3 (§6.1) to measure perceived complexity change; discuss qualitatively; include role-change as a covariate in sensitivity analysis |

---

## 12. Future Directions

- **Longitudinal extension:** extend recruitment and follow-up to 24–36 months to detect slower-accumulating effects.
- **Objective vibe-coding measure:** integrate with GitHub activity data (with consent) to estimate actual proportion of AI-generated commits, reducing reliance on self-report.
- **Intervention study:** following this observational phase, a randomised experiment could assign participants to "deliberate practice" vs. "vibe-code freely" conditions for 3 months to test causality.
- **Skill domain specificity:** extend beyond Python to JavaScript, SQL, or shell scripting to test whether effects are Python-specific or general.
- **Think-aloud thematic analysis:** if think-aloud data is collected at scale, thematic analysis of verbalised problem-solving strategies between high and low vibe-coders (distinct from the exit-survey qualitative strand already planned in §6).
- **Moderating role of programming education:** compare developers who learned to code before vs. after the widespread availability of AI assistants (i.e., pre- vs. post-2022 entrants to the field).

---

## 13. Open Science Commitments

| Commitment | Plan |
|------------|------|
| Pre-registration | OSF pre-registration before first participant session |
| Analysis script pre-registration | R analysis script deposited at OSF at pre-registration |
| Open data | Full anonymised dataset released after 12-month embargo (see high_level_plan.md §12) |
| Open materials | Challenge content released under original licences; survey instruments and codebook released alongside dataset |
| Reproducible analysis | Analysis scripts in `analysis/` directory in this repo; Docker/`renv` lockfile for reproducibility |
| Deviation reporting | Any deviation from this pre-registered plan is clearly documented in the paper with justification |

---

## 14. Ethics

- **Ethics approval:** Royal Holloway, University of London (application in progress).
- **Informed consent:** full versioned consent system implemented in-app (see high_level_plan.md §7).
- **GDPR compliance:** EU participant data handled per GDPR; data processing agreement with Hetzner (EU-based hosting).
- **Data retention:** per policy in high_level_plan.md §7.5 and §18.
- **Participant rights:** withdrawal, data deletion, and optional consent mechanisms fully implemented (see high_level_plan.md §18).
- **Interview sub-study:** the ethics application must declare that participants will be asked at exit whether they are willing to be contacted for a potential follow-up interview (`OptionalConsentRecord.consent_type = "future_contact"`, implemented in consent.0002). No interview protocol is required before launch; the instrument can be developed later under the same ethics approval. Any interviews conducted will require explicit consent; recordings deleted post-transcription; never included in the open dataset.

---

## 15. Identified Gaps (items to resolve before pre-registration)

These are open questions that must be answered or decided before the OSF pre-registration is finalised:

- [x] **Power simulation:** script exists at `analysis/power_simulation.Rmd` — knit it and update §8.1 targets based on results. Requires R packages: `lme4`, `dplyr`, `tibble`, `tidyr`, `ggplot2`, `MASS`, `knitr`, `kableExtra`, `gridExtra`, `pbmcapply`. Parallelised across available cores (1000 sims per condition); expected runtime ~3–6 min on M4 Max.
- [x] **Vibe-coding scale anchoring:** resolved by adding a complementary review-thoroughness question (*"Of the code AI generates for you, roughly what percentage do you check over carefully?"*). The two measures together yield a passive reliance index (§4.3) that is behaviourally grounded and reduces reliance on precise slider calibration. Both questions added to post-session survey via the unified question system.
- [x] **Baseline session design:** sessions are identical across all time points. The multilevel model estimates each participant's baseline ability from all sessions jointly (random intercept via partial pooling), so a noisy session 1 is handled gracefully. A different baseline structure would introduce measurement non-invariance and make session 1 timing data incomparable — particularly problematic for H2. Note in the paper that individual baselines are estimated jointly rather than from session 1 alone.
- [x] **IRT calibration timing:** IRT dropped entirely. Difficulty is handled by: (1) human-assigned 5-tier labels at import using documented per-source mapping rules (Exercism 1–10 scale → tiers, APPS introductory/interview/competition → tiers, custom challenges assigned directly); (2) cross-source tier validation at ~3 months (S4 sensitivity analysis) — aggregate pass rates per tier per source, ~50 attempts per tier-source cell sufficient. No per-challenge sample size needed. See §9 milestone and §5 S4.
- [x] **Session ordering vs. tier coverage trade-off:** ascending difficulty is retained. H1 (primary) targets Tier 1–2 everyday fluency — exactly what ascending order measures. Interleaving risks dropout at hard early challenges, which would damage longitudinal retention far more than sparse Tier 3+ data. Across 400 participants × 6 sessions, Tier 3+ data will accumulate from participants who complete more challenges, sufficient for exploratory analysis. H3 is formally downgraded to exploratory, contingent on sufficient Tier 3+ attempts accumulating.
- [x] **Handling zero vibe-coders:** vibe-coding percentage is treated as continuous in the primary model. The expected distribution is near-bimodal (heavy users vs non/low users, few in the middle) — high variance in the predictor is beneficial for power, and the model is valid regardless of predictor distribution shape. Two pre-specified sensitivity analyses: (a) binary split (≤20% = low, >20% = high) as a cleaner comparison for paper presentation; (b) quadratic term added to test for non-linearity / threshold effects, since with few participants in the middle the linearity assumption across the full range is empirically undertested.
- [x] **Minimum meaningful session for analysis:** sessions with fewer than 4 challenge attempts are excluded from the primary model — a single attempt yields accuracy of 0% or 100% (no variance), and 2–3 attempts remain very noisy. The in-app prompt has been updated to explicitly encourage completing 4–5 challenges ("For the most useful data, we'd really appreciate it if you could complete at least 4–5 challenges"). Sessions with < 4 attempts are retained in the database and reported descriptively but excluded from the multilevel model.
- [x] **Multiple comparison correction:** no formal correction applied. The primary analysis is frequentist multilevel regression (`lme4` + `lmerTest`; Satterthwaite df). Pre-registration serves as the protection against inflated false-positive rates — correction is for unplanned fishing, not pre-registered hypotheses (Lakens et al., 2018). Strict hierarchy is maintained instead: H1 is the single primary test; H1b, H2, H3, H4 are pre-registered secondary tests reported with full effect sizes and 95% CIs; exploratory analyses are clearly labelled. `brms` retained as a pre-specified robustness check if convergence issues arise with real data or if requested by reviewers.
- [x] **Pre-registration of exploratory analyses:** framework established. Exploratory analyses are pre-committed (listed in the OSF registration) but clearly labelled as hypothesis-generating, not hypothesis-testing. Paper will have two clearly labelled sections: *Confirmatory analyses* and *Exploratory analyses*.
  - **Confirmatory:** H1 (primary), H1b, H2, H4
  - **Secondary (pre-registered, lower evidentiary weight):** H5
  - **Conditionally confirmatory:** H3 — treated as confirmatory only if Tier 3+ attempts exceed 500 across all participants at analysis time; otherwise automatically downgraded to exploratory. Threshold pre-registered to prevent post-hoc reclassification.
  - **Exploratory (pre-committed, hypothesis-generating):** §4.6 variables, passive reliance index decompositions beyond H1b, qualitative themes. Pre-committed to running and reporting all regardless of outcome to prevent selective reporting (Nosek et al., 2018, PNAS).
- [x] **Exit survey implementation (Phase 1 — model):** `context = "exit"` added to `SurveyQuestion.Context` choices and migrated (surveys.0003). Phase 2 deferred: exit flow UI, withdrawal trigger, 12-month email trigger, and exit question fixtures.
- [x] **`future_contact` consent:** `FUTURE_CONTACT = "future_contact"` added to `OptionalConsentRecord.ConsentType` choices and migrated (consent.0002). Will be presented in the exit survey UI (Phase 2).
- [x] **Interview protocol:** no protocol needed before launch. Key ethics action: declare in the ethics application that participants will be asked whether they consent to being contacted for a potential follow-up interview (`OptionalConsentRecord.consent_type = "future_contact"`). The interview instrument itself can be developed later under the same ethics approval.
- [x] **Qualitative analysis plan:** same paper, convergent mixed-methods design (Creswell & Plano Clark, 2018). Reflexive thematic analysis of exit survey responses and interviews reported as a qualitative supplement section alongside the quantitative findings; strands integrated at the interpretation stage. Fallback only if interviews run significantly later: submit quant paper first, qual as follow-up — but this is not the plan.
