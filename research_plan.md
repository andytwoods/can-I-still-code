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

---

## 2. Hypotheses

All hypotheses are directional and pre-registered. The key causal claim is that vibe coding displaces deliberate Python practice, reducing the retrieval strength of manual coding skills over time (cf. memory reconsolidation, desirable difficulties literature).

### Primary hypotheses

**H1 (core):** Participants who report a higher vibe-coding percentage will show a steeper decline in challenge accuracy over time (as measured by `tests_passed / tests_total`), after controlling for baseline ability, challenge difficulty, and total coding hours.

**H2:** Participants who report a higher vibe-coding percentage will show a steeper increase in challenge completion time over time (as measured by `log(active_time_seconds)`), after the same controls.

### Secondary hypotheses

**H3:** The negative effect of vibe coding on accuracy over time (H1) will be larger for Tier 1–2 challenges than for Tier 3–5 challenges. Rationale: AI tools most thoroughly replace basic syntax and boilerplate recall; higher-tier problems require algorithmic reasoning that AI augments rather than replaces entirely.

> **Power caveat:** With ascending difficulty ordering and expected session dropout at challenge 4–6, the majority of attempts will be Tier 1–2 and Tier 3+ data will be sparse. H3 may be underpowered or untestable unless session design is adjusted (see §14 gap). If Tier 3–5 data are insufficient, H3 is downgraded to exploratory.

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
| Session cadence | Maximum one session per 28 days; no minimum frequency. Participants may complete as few as 2 sessions with any gap between them. |
| Session structure | 1–10 Python coding challenges per session; participant-controlled |
| Blinding | Participants are not told specific hypotheses beyond "we are studying AI coding and skill" |

This is a **purely observational study** — there is no random assignment to vibe-coding conditions. Causal inference is therefore limited; the study can establish longitudinal associations and is powered to detect moderation, but cannot rule out all confounds. See §10 (Limitations) for full discussion.

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

### 4.3 Primary Independent Variable

| Variable | Operationalisation | Data field(s) | Time-varying? |
|----------|--------------------|---------------|---------------|
| **Vibe-coding intensity** | Self-reported % of coding time that is AI-assisted | `SurveyResponse` for `post_session` question "What percentage of your coding time is currently vibe coding?" | Yes — updated each session |

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

A Bayesian multilevel regression model estimated with `brms` (R) using Stan as the backend:

```
accuracy_logit ~ vibe_coding_pct * months_since_baseline
                 + hours_per_week
                 + difficulty_tier
                 + leetcode_familiarity
                 + device_type
                 + distraction_free
                 + (1 + months_since_baseline | participant_id)
                 + (1 | challenge_id)
```

- **Random intercept + slope for participant:** captures individual baseline ability and individual rate of change over time.
- **Random intercept for challenge:** captures item-level difficulty beyond the fixed tier rating.
- **Key interaction:** `vibe_coding_pct × months_since_baseline` — does higher vibe-coding predict a steeper skill trajectory (positive = improvement, negative = decline)?
- **Time-varying predictors** (`vibe_coding_pct`, `hours_per_week`) use the value reported at the session containing each attempt.
- **Vibe-coding percentage** is centred and scaled (z-score across all observations) to aid interpretation and MCMC efficiency.
- **Months since baseline** is scaled to units of 3 months to make coefficients more interpretable (one unit = one quarter).

### 5.2 Prior Specification (weakly informative)

| Parameter | Prior | Justification |
|-----------|-------|---------------|
| Intercept | `Normal(0, 1)` on logit scale | Equivalent to 50% accuracy ± plausible range |
| Fixed slopes | `Normal(0, 0.5)` | Regularising; allows moderate effects |
| SD of random intercepts (participant) | `HalfNormal(0.5)` | Substantial between-person variation expected |
| SD of random slopes (participant) | `HalfNormal(0.25)` | Smaller — slope variation is a secondary quantity |
| SD of random intercepts (challenge) | `HalfNormal(0.5)` | Substantial between-item variation expected |
| Correlation of random effects | `LKJ(2)` | Weakly regularising; slight pull toward uncorrelated |

Prior predictive checks will be run before data collection to confirm priors generate plausible accuracy distributions (0–100%).

### 5.3 Secondary Models

**S1 — Speed model:** Same random effects structure, with `log(active_time_seconds)` as the outcome and a Gaussian likelihood. Attempts with `active_time_seconds < 10` or `> 3600` are excluded as implausible.

**S2 — Tier moderation model:** Extends the primary model with a three-way interaction `vibe_coding_pct × months_since_baseline × difficulty_tier_low_binary` (Tier 1–2 vs. Tier 3–5), testing H3.

**S3 — Item Response Theory:** A 2PL IRT model (`brms` using `bernoulli` likelihood with item difficulty and discrimination parameters) to estimate latent ability per participant per time point. Latent ability estimates are then used as the outcome in a simplified version of the primary longitudinal model.

---

## 6. Inclusion and Exclusion Criteria

### 6.1 Participant-level inclusion

- Must have completed ≥ 2 sessions (to have a baseline and at least one follow-up).
- Must have answered the vibe-coding percentage question in ≥ 2 sessions.
- Must have given valid consent and not withdrawn before analysis.

### 6.2 Participant-level exclusion

- Staff / superuser accounts.
- Participants with `withdrawn_at` or `deletion_requested_at` set.
- Participants with evidence of systematic result fabrication (see §6.3).

### 6.3 Attempt-level exclusion (pre-specified sensitivity analysis)

The **primary analysis** uses all valid attempts. A **sensitivity analysis** re-runs the model excluding:

- Attempts where `paste_ratio > 0.8` AND the attempt is correct.
- Attempts with `active_time_seconds` below the 5th percentile for that challenge.
- Attempts with `technical_issues = True`.
- Sessions completed on phone or tablet (device-type sensitivity check).
- Sessions where `distraction_free = "no"`.

If results are materially different between primary and sensitivity analyses, this is reported as a key finding requiring discussion.

---

## 7. Power and Sample Size

### 7.1 Targets

| Target | Value | Justification |
|--------|-------|---------------|
| Minimum participants | 200 | Provides adequate variance in vibe-coding intensity (expected bimodal distribution) |
| Minimum sessions per participant | 2 | Baseline + at least one follow-up; sufficient for a change score |
| Study duration | 12 months | Minimum time for detectable skill change if effect exists |
| Expected total challenge attempts | ~4,000–8,000 | ~4–6 attempts per session (expected; participants are likely to quit when challenges get harder) × 2–5 sessions × 200 participants |
| Expected Tier 3–5 attempts | Low — sparse | With ascending difficulty ordering, participants who stop at challenge 4–6 will rarely reach Tier 3 and almost never Tier 4–5 (see §10 limitation) |

### 7.2 Minimum Effect Size of Interest (MESI)

Based on prior literature on skill decay (spacing effects, desirable difficulties), we consider a meaningful effect to be:

- **Accuracy:** a change of ≥ 5 percentage points per 6 months at the highest vibe-coding intensity (100%) relative to zero vibe-coding.
- **Speed:** a change of ≥ 15% in `active_time_seconds` per 6 months under the same contrast.

Effects smaller than these are considered practically insignificant for the claims being made, even if statistically credible.

### 7.3 Simulation-Based Power Analysis

Before launch: run simulation-based power analysis using `brms` or `simr`:

1. Simulate datasets under the MESI (§7.2) with the expected data structure (unbalanced, varying N sessions per participant).
2. Fit the primary model to each simulated dataset.
3. Calculate the proportion of simulations where the 95% CI for the key interaction excludes zero.
4. Target ≥ 80% power; adjust recruitment targets if needed.

Results of the power simulation to be documented in `analysis/power_simulation.R` and appended to this document before pre-registration.

---

## 8. Analysis Timeline

| Milestone | When |
|-----------|------|
| Power simulation complete | Before recruitment opens |
| OSF pre-registration submitted | Before first participant completes first session |
| Interim descriptive analysis | 6 months post-launch (N, retention, covariate distributions) |
| Primary analysis | After ≥ 12 months of data AND ≥ 200 participants with ≥ 3 sessions |
| Sensitivity analyses | Immediately after primary analysis |
| Exploratory analyses | After pre-registered analyses are finalised and locked |
| Dataset embargo lifted | 12 months after first completed session |
| Paper submission target | Within 6 months of primary analysis |

---

## 9. Planned Paper Structure

Mapping research questions and hypotheses to paper sections:

### Introduction
- Background: rapid adoption of AI coding assistants; vibe coding as an emerging practice
- Theoretical framing: skill decay from disuse (cognitive science); desirable difficulties; retrieval practice
- Gap: no longitudinal empirical data on the relationship between AI coding assistance and manual coding skill
- Research questions (§1) and directional hypotheses (§2)

### Method
- Participants and recruitment
- Study design (§3)
- Measures: challenges (difficulty tiers, sources, IRT calibration), survey instruments (all SurveyQuestion items used)
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
- Limitations (§10)
- Future directions (§11)

---

## 10. Limitations

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
| **Sparse Tier 3–5 data** | Challenges are presented in ascending difficulty order; participants who stop at challenge 4–6 complete only Tier 1–2. Tier 3+ attempts will be rare, weakening H3 and IRT parameter estimation for higher-tier items | Report actual Tier 3–5 attempt counts before running S2 and S3 models; if sparse, downgrade H3 to exploratory and acknowledge limited generalisability to harder challenges |

---

## 11. Future Directions

- **Longitudinal extension:** extend recruitment and follow-up to 24–36 months to detect slower-accumulating effects.
- **Objective vibe-coding measure:** integrate with GitHub activity data (with consent) to estimate actual proportion of AI-generated commits, reducing reliance on self-report.
- **Intervention study:** following this observational phase, a randomised experiment could assign participants to "deliberate practice" vs. "vibe-code freely" conditions for 3 months to test causality.
- **Skill domain specificity:** extend beyond Python to JavaScript, SQL, or shell scripting to test whether effects are Python-specific or general.
- **Qualitative component:** if think-aloud data is collected at scale, thematic analysis of verbalised problem-solving strategies between high and low vibe-coders.
- **Moderating role of programming education:** compare developers who learned to code before vs. after the widespread availability of AI assistants (i.e., pre- vs. post-2022 entrants to the field).

---

## 12. Open Science Commitments

| Commitment | Plan |
|------------|------|
| Pre-registration | OSF pre-registration before first participant session |
| Analysis script pre-registration | R analysis script deposited at OSF at pre-registration |
| Open data | Full anonymised dataset released after 12-month embargo (see high_level_plan.md §12) |
| Open materials | Challenge content released under original licences; survey instruments and codebook released alongside dataset |
| Reproducible analysis | Analysis scripts in `analysis/` directory in this repo; Docker/`renv` lockfile for reproducibility |
| Deviation reporting | Any deviation from this pre-registered plan is clearly documented in the paper with justification |

---

## 13. Ethics

- **Ethics approval:** Royal Holloway, University of London (application in progress).
- **Informed consent:** full versioned consent system implemented in-app (see high_level_plan.md §7).
- **GDPR compliance:** EU participant data handled per GDPR; data processing agreement with Hetzner (EU-based hosting).
- **Data retention:** per policy in high_level_plan.md §7.5 and §18.
- **Participant rights:** withdrawal, data deletion, and optional consent mechanisms fully implemented (see high_level_plan.md §18).

---

## 14. Identified Gaps (items to resolve before pre-registration)

These are open questions that must be answered or decided before the OSF pre-registration is finalised:

- [ ] **Power simulation:** run and document in `analysis/power_simulation.R`; confirm whether N=200 / 3 sessions is sufficient or whether targets need revising.
- [ ] **Vibe-coding scale anchoring:** the 0–100% slider (profile Q20, post-session) needs concrete anchor examples (e.g., "0% = I write all code myself; 50% = roughly equal; 100% = AI writes everything, I only review"). Without anchors, inter-participant comparability is limited.
- [ ] **Baseline session design:** the first session establishes each participant's baseline. Should the baseline session have a different structure (e.g., more challenges, no time pressure) to get a more stable estimate of initial ability? Currently it's identical to follow-up sessions.
- [ ] **IRT calibration timing:** the IRT model (§5 S3) requires sufficient data to estimate item parameters. Plan for when to run the first IRT calibration (after N attempts per challenge?), and how to handle challenges with few responses in early months. Note: Tier 3–5 items may never accumulate sufficient responses if participants routinely quit before reaching them.
- [ ] **Session ordering vs. tier coverage trade-off:** ascending difficulty means participants who quit at challenge 4–6 never see Tier 3–5. Consider alternatives: (a) interleaved ordering (e.g. T1, T2, T1, T2, T3, T2, T3, T4, T3, T5) to guarantee at least one harder item early; (b) a fixed "anchor" Tier 3 challenge always presented as challenge 3 to ensure some harder-tier data per session. Decide before pre-registration as it affects H3 testability.
- [ ] **Handling zero vibe-coders:** participants who report 0% vibe coding at every session form the natural comparison group but may be a small and unusual subgroup (non-adopters). Decide whether to model vibe-coding as continuous or create ordered groups (0%, 1–25%, 26–50%, 51–75%, 76–100%).
- [ ] **Minimum meaningful session for analysis:** a session with only 1 challenge attempted has very noisy accuracy (0 or 100%). Define a minimum number of challenge attempts per session for inclusion in the primary model (suggest: ≥ 3 attempts).
- [ ] **Multiple comparison correction:** the primary model has one pre-specified test (H1). Secondary models (H2, H3, H4) and sensitivity analyses are separate model fits, not additional coefficients in the primary model. State explicitly whether Bayesian posterior probabilities for secondary models will be interpreted with any adjustment.
- [ ] **Pre-registration of exploratory analyses:** clarify which analyses are confirmatory (H1–H5) and which are explicitly flagged as exploratory to prevent inflated claims in the paper.
