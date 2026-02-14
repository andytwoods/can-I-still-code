# High-Level Plan: Coding Skill Longitudinal Assessment App

## 1. Purpose

A longitudinal, citizen-science research tool designed to measure whether **vibe coding** (AI-assisted coding) leads to coding skill degradation over time. Participants periodically complete short Python coding challenges while self-reporting their coding habits. The resulting dataset — openly shared — supports **Bayesian multilevel regression** modelling and invites the broader community to contribute analyses.

## 2. Target Users

- Developers with existing Python coding experience.
- Varying levels of vibe-coding adoption (from none to heavy).
- Recruited broadly (social media, developer communities, university networks).

## 3. Core User Flow

1. **Register / Log in** — create a profile, provide baseline demographic and coding-habit data.
2. **Assessment session** — complete Python coding challenges (participant chooses how many, up to 10 per session).
3. **Post-session survey** — update self-report measures (vibe-coding frequency, hours coding per week, etc.).
4. **Explore your results** — rich, interactive graphs showing personal performance trends over time.
5. **Return monthly** — repeat steps 2–4 (minimum 28 days between sessions) to build longitudinal data.

---

## 4. Session Structure and Flexibility

### 4.1 Participant-Driven Sessions
- Each session offers **up to 10 challenges**. The participant can stop at any point (minimum 1 to record a valid session).
- Challenges are presented one at a time. After each challenge is submitted (or skipped), the participant sees a simple prompt:

  > **Nice work! Ready for another?**
  >
  > [ Another challenge ] · [ I'm done for today ]
  >
  > *Challenge 3 of up to 10 · Session saves automatically*

- **Between each challenge**, before the "another?" prompt, the participant answers a short set of **post-challenge reflection questions** (see §5.5).
- While working on a challenge, a subtle **[ Stop session ]** link is always visible (e.g. top-right corner). Clicking it confirms: *"End session? Your previous answers are already saved. This challenge will be recorded as skipped."* The participant then goes to the post-session survey.
- The tone is encouraging but low-pressure — no guilt for stopping early, no countdown creating anxiety.
- On the final (10th) challenge, the prompt changes to a session-complete message instead.
- If the participant clicks "I'm done", they go straight to the post-session survey and then their results dashboard.
- This flexibility respects participants' time while still generating usable data from shorter sessions.

### 4.2 Session Environment Guidelines
Before each session starts, a brief reminder is shown:

> **Before you begin**
>
> For the most reliable results, please try to:
> - Find a **quiet, distraction-free** environment — just like you would for focused coding.
> - Keep conditions **similar each time** (e.g. same time of day, same type of setting).
> - Set aside **3–20 minutes** of uninterrupted time.
> - **No AI assistants, no Googling** — this is about what *you* can do from memory.
>
> *This isn't a test you can fail. Consistent conditions just help us (and you) track genuine change over time.*

- The participant must tick a checkbox acknowledging they've read this before starting (lightweight — not a multi-page consent flow each time).
- This is a **guideline, not enforced** — we can't control their environment, but the reminder primes good behaviour.
- Optionally, after the session, ask: *"Were you able to work without distractions?"* (Yes / Mostly / No) — this becomes a covariate we can include in the analysis to account for noisy sessions.

### 4.3 Session Frequency
- **Minimum 28 days between sessions** — enforced server-side. Uses days-since-last-session rather than calendar month boundaries, which avoids time zone confusion.
- No minimum frequency; participants may skip months and return later.
- Reminder emails (opt-in) sent if a participant hasn't completed a session in the past month.

### 4.4 Why This Flexibility Matters
- Rigid session structures cause dropout. Letting participants choose effort level per session improves retention.
- The resulting **unbalanced data** (varying numbers of challenges per session, varying numbers of sessions per participant) is handled naturally by the Bayesian analysis framework (see §10).

---

## 5. Coding Challenges

### 5.1 Format
- A partially completed Python function/snippet with a docstring/description, where the participant fills in the missing logic.
- Code runs **in the browser** — no server-side execution needed (see §6).
- Validated against a suite of test cases; pass/fail plus timing recorded.

### 5.1a Timing
Time-per-challenge is a key outcome variable. We record it with precision:

- **Timer starts** when the challenge is displayed (code skeleton visible).
- **Timer stops** when the participant clicks "Submit" or "Skip".
- A **visible elapsed-time indicator** is shown (e.g. a small clock or `mm:ss` in the corner) — not as pressure, but so participants can self-pace. This can be toggled off in user preferences if it causes anxiety.
- **Idle detection:** if the browser tab loses focus for >30 seconds, or there is no keystroke for >2 minutes, that interval is flagged as `idle_time_seconds` on the attempt. This lets us distinguish "took 8 minutes thinking hard" from "took 8 minutes because they went to make tea."
- Both `time_taken_seconds` (wall clock) and `active_time_seconds` (wall clock minus idle) are stored. Analysis can use either.

### 5.1b Think-Aloud Protocol (Optional)

Participants can opt in to a **concurrent think-aloud** — verbalising their thought process while solving each challenge. This is a well-established cognitive psychology method (Ericsson & Simon, 1993) that yields rich qualitative data about problem-solving strategies.

#### How It Works
- At session start, if the participant has opted in (via profile settings), a prompt asks for **microphone permission**.
- During each challenge, audio is recorded via the browser's MediaRecorder API.
- A small **recording indicator** (pulsing dot) is visible so the participant knows it's active.
- A brief on-screen prompt reminds them: *"Think out loud — say what you're thinking as you work through this."*
- Audio is uploaded to the server as a compressed file (e.g. WebM/Opus) after each challenge submission.

#### Data Pipeline
- **Raw audio** is stored per challenge attempt (linked via `ChallengeAttempt` FK).
- **Speech-to-text transcription** is run asynchronously (Huey background task) using an STT service (e.g. OpenAI Whisper API, or self-hosted Whisper).
- **Transcripts** are stored alongside the audio, enabling:
  - Qualitative thematic analysis of problem-solving strategies.
  - Automated coding of verbalised confusion, strategy shifts, or references to AI habits.
  - Comparison of think-aloud content between high and low vibe-coders.

#### Data Model Additions

```
ThinkAloudRecording
  - challenge_attempt (FK → ChallengeAttempt)
  - audio_file (FileField — compressed audio)
  - duration_seconds (float)
  - transcript (TextField — populated async by STT)
  - transcription_status (pending / processing / complete / failed)
  - transcribed_at (datetime, nullable)
```

#### Ethical and Practical Notes
- **Strictly opt-in** — defaulting to off. Clearly explain what the audio is used for.
- Participants can **opt out at any time**, and request deletion of their audio recordings.
- Audio is **never publicly released** — the open dataset (§12) includes only anonymised transcripts (if the participant consents to transcript sharing) or excludes think-aloud data entirely.
- Think-aloud can slightly alter performance (dual-task cost). This is a known trade-off; we record whether think-aloud was active as a covariate in the analysis.
- **Not required for MVP** — this is a Phase 2/3 feature, but designing for it now avoids schema changes later.

### 5.2 Difficulty Tiers

LeetCode "Easy" is still algorithmic (hash maps, two pointers, etc.) and would exclude or frustrate many working developers whose day-to-day coding doesn't involve algorithm puzzles. To measure **practical coding fluency** across a wide ability range, we use a **5-tier difficulty system**:

#### Tier 1 — Fundamentals (~30 seconds–2 minutes)
Core Python literacy. Any working developer should nail these quickly; the signal is in *how quickly*.

Example tasks:
- Complete a list comprehension that filters even numbers.
- Fix a dictionary lookup that uses the wrong method.
- Write a string formatting expression using an f-string.
- Fill in the correct slice to reverse a list.
- Complete a `for` loop that enumerates a list with index and value.

Sources: [W3Schools Python Exercises](https://www.w3schools.com/python/python_exercises.asp), [PYnative Basic Exercises](https://pynative.com/python-basic-exercise-for-beginners/).

#### Tier 2 — Practical Fluency (~1–3 minutes)
Bread-and-butter tasks a professional developer does routinely, but requiring more than one-line syntax recall.

Example tasks:
- Write a function that groups a list of dicts by a key.
- Complete a class `__init__` and `__repr__` method.
- Implement simple error handling: catch a specific exception and return a default.
- Parse a CSV-like string into a list of tuples.
- Write a decorator that logs function calls.

Sources: [PYnative Data Structure Exercises](https://pynative.com/python-data-structure-exercise-for-beginners/), [Dataquest Python Practice](https://www.dataquest.io/blog/python-practice/).

#### Tier 3 — Intermediate Problem-Solving (~3–6 minutes)
Requires combining multiple concepts or thinking through a non-trivial approach; equivalent to LeetCode Easy.

Example tasks:
- Two Sum (find indices of two numbers that add to a target).
- Validate balanced parentheses.
- Merge two sorted lists.
- Implement a simple stack or queue with specific operations.

Sources: [Exercism Python track](https://github.com/exercism/python) (practice exercises), [APPS dataset](https://github.com/hendrycks/apps) (introductory tier).

#### Tier 4 — Algorithmic (~5–10 minutes)
Classic algorithm/data-structure problems; equivalent to LeetCode Medium.

Example tasks:
- Binary search with a twist (rotated sorted array).
- BFS/DFS on a graph or tree.
- Dynamic programming (e.g. coin change, longest subsequence).

Sources: [APPS dataset](https://github.com/hendrycks/apps) — interview tier.

#### Tier 5 — Advanced (~8–10+ minutes)
Complex algorithmic challenges; equivalent to LeetCode Hard. Included for ceiling measurement — most participants won't reach these.

Sources: [APPS dataset](https://github.com/hendrycks/apps) — competition tier.

#### Why This Matters for the Research
- **Floor effects are as problematic as ceiling effects.** If every challenge is LeetCode-style, a competent web developer who doesn't grind algorithms will score poorly at every time point, giving us no variance to detect change.
- **Tier 1–2 challenges measure the skill most likely to atrophy** — everyday Python fluency. If vibe coding means you rarely write basic Python by hand anymore, these are the skills that degrade first.
- **The IRT model (§10.3) benefits from a wide difficulty spread** — it needs items that discriminate across the full ability range, not just the top end.

### 5.3 Challenge Source

All challenge sources use **permissive open-source licences** (MIT or CC BY-NC-SA for non-commercial research use). We deliberately avoid LeetCode problems — their ToS prohibits reproduction, and HuggingFace datasets that scrape LeetCode content carry legal risk.

| Tier | Source | Licence | Notes |
|------|--------|---------|-------|
| 1–2 | [Exercism Python track](https://github.com/exercism/python) | **MIT** (code/tests), CC BY-NC-SA (descriptions) | ~140 exercises with test suites. Mix of concept and practice exercises. Ideal for practical fluency challenges. |
| 1–2 | Custom-authored + adapted from [PYnative](https://pynative.com/python-exercises-with-solutions/), [W3Schools](https://www.w3schools.com/python/python_exercises.asp), [W3Resource](https://www.w3resource.com/python-exercises/) | Adapted (original descriptions) | Hundreds of basic/intermediate exercises. We rewrite descriptions and author test cases. |
| 2–5 | [APPS dataset](https://github.com/hendrycks/apps) (Hendrycks et al., NeurIPS 2021) | **MIT** | 10,000 Python problems curated from open-access sites (Codewars, AtCoder, Kattis, Codeforces). 131K test cases, 232K human solutions. Three difficulty levels: introductory, interview, competition. |
| 3–5 | [Project Euler](https://projecteuler.net/) | **CC BY-NC-SA 4.0** | 900+ maths/programming problems. Useful for harder tiers but math-heavy; use selectively. |
| All  | [python-coding-challenges GitHub topic](https://github.com/topics/python-coding-challenges) | Varies | Various community repos; vet licence per problem. Good for filling gaps. |

**Target:** Curate ~150–250 problems total (~50 Tier 1, ~50 Tier 2, ~50 Tier 3, ~30 Tier 4, ~20 Tier 5). Assign each an internal difficulty score; refine with IRT after data collection.

### 5.4 Challenge Selection per Session

#### Random Selection — No Repeats
- Challenges are **randomly selected** for each participant from the available pool.
- A participant **never sees the same challenge twice** — once a challenge has been presented (whether completed or skipped), it is permanently excluded from that participant's future sessions.
- This is enforced server-side: the selection algorithm queries all `ChallengeAttempt` records for the participant and excludes those challenge IDs from the pool before sampling.

#### Selection Algorithm
1. Query the full pool of active challenges.
2. Exclude any challenge the participant has already been shown (via `ChallengeAttempt` records, including skipped attempts).
3. From the remaining pool, randomly sample up to 10 challenges using the **tier distribution**: 3 Tier 1, 3 Tier 2, 2 Tier 3, 1 Tier 4, 1 Tier 5 — tunable via admin settings.
4. If a tier's pool is exhausted for that participant (e.g. they've seen all Tier 1 problems), fill the remaining slots from adjacent tiers.
5. Sort the selected challenges in **ascending difficulty order** so participants build confidence before hitting harder problems.
6. The selected set is locked at session start and stored on the `Session` record, so it doesn't change if the participant pauses mid-session.

#### Pool Exhaustion
- With ~200 problems and 10 per session, a participant can complete ~20 sessions before exhausting the pool.
- At monthly cadence, that's ~20 months of unique challenges — well within the study timeline.
- If a participant nears pool exhaustion, inform them: *"You've completed most of our challenges! We're adding new ones regularly."*
- Expanding the challenge pool over time (§17) mitigates this for long-running participants.

#### Why Random Selection Matters
- **No two participants get the same session** — this prevents answer-sharing and means each participant's data is partially unique, which the IRT model (§10.3) leverages to estimate item difficulty more robustly.
- **No examiner bias** — no one hand-picks which challenges a participant sees.
- Consider adaptive testing later (selecting difficulty based on prior performance) as an enhancement, but random selection is the baseline.

### 5.5 Post-Challenge Reflection Questions

After submitting (or skipping) each challenge, the participant answers 2–4 quick quantitative questions before seeing the "another?" prompt. These must be fast — **slider or Likert scale, no free text** — so they don't break flow.

#### Default Questions (initial launch)

| # | Question | Scale |
|---|----------|-------|
| 1 | *How difficult did you find that challenge?* | 1 (Very easy) – 7 (Very hard) |
| 2 | *Would this have been easier for you before you started vibe coding?* | 1 (Much easier before) – 4 (No difference) – 7 (Much easier now) |
| 3 | *How confident are you that your answer is correct?* | 1 (Not at all) – 7 (Completely) |

- Questions 1 and 3 are standard subjective difficulty/metacognition measures.
- Question 2 directly taps the participant's perception of skill change — a valuable complement to the objective performance data.

#### Admin-Configurable via Unified Question System

Post-challenge questions are **not hard-coded**. They use the **unified question system** (see §8.2) with `context = "post_challenge"`. This means they share the same `SurveyQuestion` / `SurveyResponse` models as profile questions and post-session habit questions — one system, one admin interface, one data format.

- **Add new questions at any time** via the admin — they appear in the next session for all participants.
- **Retire old questions** by setting `is_active = False` — historical responses are preserved.
- **Reorder questions** by changing `display_order`.
- **No code deployment needed** to change the question set.
- The citizen-science community (§11) can propose new questions; admins review and add them.

#### Design Considerations
- Keep it to **2–4 questions max** per challenge to avoid survey fatigue (participants answer these up to 10 times per session).
- All questions use the same visual widget (a horizontal slider or tappable scale) for speed and consistency.
- Responses are optional — if a participant clicks "skip" on the reflection, the challenge attempt still records fine.

---

## 6. In-Browser Python Execution (Pyodide + WebAssembly)

Use **[Pyodide](https://pyodide.org/)** — a precompiled CPython distribution targeting WebAssembly:

- Load Pyodide from CDN (`<script>` tag); no compilation step in our build.
- Participant's code runs entirely client-side in a Web Worker (no server round-trip, no sandboxing concerns on the backend).
- Test cases also execute client-side; results (pass/fail, stdout, stderr, elapsed time) are sent to the server as structured JSON.
- Pyodide supports the Python standard library plus NumPy, etc., but for this use case vanilla Python is sufficient.

### Integrity Monitoring and Cheating Detection

Because code runs client-side, participants could use AI tools, paste solutions from elsewhere, or fabricate results. We take a **detect-and-flag** approach rather than trying to prevent cheating outright — the data is used for research, so flagging suspicious attempts as covariates is more valuable than blocking them.

#### Client-Side Telemetry (captured per challenge attempt)

Three signals, stored as fields on `ChallengeAttempt` (no separate model needed):

```
ChallengeAttempt (additional integrity fields)
  - paste_count (int — number of paste events)
  - paste_total_chars (int — total characters pasted)
  - keystroke_count (int — total keystrokes in the editor)
  - tab_blur_count (int — times the browser tab lost focus)
```

These four fields are cheap to capture (browser `paste` and `blur` events) and together cover the two key cheating signals: **pasting a solution** (high paste chars, low keystrokes) and **looking something up** (tab blurs). A derived `paste_ratio` (`paste_total_chars / len(submitted_code)`) is computed at analysis time.

#### Outlier Detection (at analysis time)

- Flag attempts where `paste_ratio > 0.8` and the answer is correct.
- Flag attempts with `active_time_seconds` below the 5th percentile for that challenge.
- Flagged attempts are **not auto-excluded** — primary analysis runs on all data, sensitivity analysis re-runs without flagged attempts to check robustness.
- Participants are **not notified** of flags.

---

## 7. Informed Consent and Ethical Permissions

### 7.1 Consent Gate

Participation is **blocked until consent is given**. After account creation, the very first screen is a consent form — not a terms-of-service wall, but a genuine informed-consent document in plain language explaining:

1. **What this study is about** — investigating the relationship between AI-assisted coding and coding skill over time.
2. **What participation involves** — periodic coding sessions, surveys, optional audio recording.
3. **What data is collected** — challenge responses, timing, survey answers, optionally audio/transcripts.
4. **How data is used** — anonymised for research, aggregated on the public site, full anonymised dataset released after 12 months.
5. **Who can see your data** — you see your own data; the public sees only aggregates; the anonymised dataset is released to participants after the embargo.
6. **Your rights** — you can withdraw at any time, request data deletion, and decline optional elements (think-aloud, specific survey questions) without affecting your participation.
7. **Risks** — minimal; the main risk is time spent. No deception involved.
8. **Contact** — who to contact with questions or complaints.

The consent form is **admin-editable** (stored in the database, not hard-coded in a template) so it can be corrected, updated, or expanded as the study evolves or as an ethics board requires changes.

### 7.2 Consent Data Model

Consent is **explicitly recorded per version** — if the consent form is updated, participants are asked to re-consent to the new version before their next session.

```
ConsentDocument
  - version (CharField, e.g. "1.0", "1.1")
  - title (CharField)
  - body (TextField — the full consent text, supports markdown)
  - is_active (bool — only one version should be active at a time)
  - published_at (datetime)
  - created_at / updated_at

ConsentRecord
  - participant (FK -> Participant)
  - consent_document (FK -> ConsentDocument)
  - consented (bool — True = agreed, False = declined)
  - consented_at (datetime)
  - ip_address (GenericIPAddressField — for audit trail)
  - user_agent (CharField — for audit trail)

OptionalConsentRecord
  - participant (FK -> Participant)
  - consent_type (CharField, choices: "think_aloud_audio", "transcript_sharing", "reminder_emails")
  - consented (bool)
  - consented_at (datetime)
  - withdrawn_at (datetime, nullable — if they later opt out)
```

### 7.3 Consent Flow

1. **First visit after registration:** full consent form displayed. Participant must actively tick "I have read and agree" and click "Give consent" to proceed. No pre-ticked checkboxes.
2. **If they decline:** they cannot access sessions. A message explains what they'd need to consent to in order to participate, with a link to re-read and consent later if they change their mind.
3. **Optional consents** (think-aloud audio, transcript sharing, reminder emails) are presented as separate, clearly labelled opt-in checkboxes — declining these does not prevent participation.
4. **Consent version update:** if the `ConsentDocument` is updated (new active version), any participant whose most recent `ConsentRecord` is for an older version sees the updated form before their next session. They must re-consent to continue.
5. **Withdrawal:** participants can withdraw consent via their profile settings at any time. This sets a `withdrawn_at` timestamp and prevents further sessions. Data deletion is handled per the policy in §18.

### 7.4 Admin Panel
- Admins can **create new consent document versions** with full markdown text.
- Admins can **view an audit log** of all consent records (who consented, when, to which version).
- Admins can **export consent records** for ethics board reporting.
- Optional consents are also visible and exportable.

---

## 8. Participant Profile and Demographics

### 8.1 When It's Collected
- **At registration** (after consent): participants complete an intake questionnaire covering demographics, coding background, and AI tool usage.
- **Periodically reviewable:** participants can update their profile between sessions (e.g. if they change jobs or start using new tools). Changes are **versioned** — we store each snapshot so we can see what their profile looked like at the time of each session.

### 8.2 Unified Question System

All questionnaire data in the study — profile intake, post-challenge reflections, and post-session habit surveys — uses a **single, consolidated question/response system** rather than separate models per context. This avoids duplicated logic, simplifies the admin interface, and ensures consistent data export.

```
SurveyQuestion
  - text (CharField — the question wording)
  - help_text (CharField, optional — clarifying note shown below the question)
  - question_type (choices: "text", "number", "single_choice", "multi_choice", "scale")
  - choices (JSONField, nullable — list of options for single/multi choice questions)
  - scale_min (int, nullable — for scale questions, e.g. 1)
  - scale_max (int, nullable — for scale questions, e.g. 7)
  - min_label (CharField, nullable — e.g. "Very easy")
  - max_label (CharField, nullable — e.g. "Very hard")
  - mid_label (CharField, nullable — e.g. "No difference", shown at midpoint)
  - context (choices: "profile", "post_challenge", "post_session")
  - category (CharField, nullable — for UI grouping, e.g. "Demographics", "Coding Background")
  - is_required (bool — must they answer to proceed?)
  - is_active (bool — toggle on/off without deleting)
  - display_order (int)
  - created_at / updated_at

SurveyResponse
  - participant (FK -> Participant)
  - question (FK -> SurveyQuestion)
  - value (TextField — stores the response; JSON for multi-choice, string for everything else)
  - answered_at (datetime)
  - -- Context FKs (nullable — exactly one is set depending on question.context):
  - session (FK -> Session, nullable)              -- set for post_session questions
  - challenge_attempt (FK -> ChallengeAttempt, nullable)  -- set for post_challenge questions
  - supersedes (FK -> self, nullable)              -- for profile questions that get updated
```

#### How the Contexts Work

| Context | When shown | Linked to | Example questions |
|---------|-----------|-----------|-------------------|
| `profile` | Registration intake + profile page | Participant only | Age, gender, years coding, LeetCode familiarity |
| `post_challenge` | After each challenge attempt | ChallengeAttempt | "How difficult?", "Harder since vibe coding?" |
| `post_session` | End of session (replaces old CodingHabitSurvey) | Session | Vibe coding %, hours/week, tools used, distractions |

#### Benefits of Consolidation
- **One admin interface** to manage all questions across all contexts.
- **One export format** — every response is a row in the same table, filterable by `context`.
- **Consistent rendering** — the front-end uses a single question-rendering component that reads `question_type` and renders the appropriate widget (text field, dropdown, slider, checkbox group).
- **Easy to add new contexts later** (e.g. "post_study_exit" for a debrief survey) without schema changes.
- **Profile responses track changes** via `supersedes` — useful because someone's coding habits may shift during the study.

This means:
- **Add new questions at any time** — they appear in the appropriate context for all participants.
- **Retire questions** by setting `is_active = False` — historical responses preserved.
- **No code deployment needed** to change any question set across the entire study.

### 8.3 Default Questions (Initial Launch)

#### Demographics

| # | Question | Type | Options / Notes |
|---|----------|------|-----------------|
| 1 | *What is your age?* | number | Free entry (years). Stored as exact age; can be binned for reporting. |
| 2 | *How do you describe your gender?* | single_choice | "Man", "Woman", "Non-binary", "Prefer to self-describe" (free text), "Prefer not to say". Following [inclusive survey best practices](https://www.alchemer.com/resources/blog/how-to-write-survey-gender-questions/) — not a binary M/F, includes self-describe option, never mandatory. |
| 3 | *Where are you based?* | single_choice | Country dropdown. Useful for controlling for regional tech culture differences. |
| 4 | *Is English your first language?* | single_choice | "Yes", "No — but I'm fluent", "No — I'm conversational", "No — I find English challenging". Important because challenge descriptions are in English; language barrier could confound difficulty ratings. |
| 5 | *What is your highest level of education?* | single_choice | "Self-taught / no formal education", "High school", "Bootcamp / vocational", "Bachelor's degree", "Master's degree", "PhD / Doctorate", "Prefer not to say". |
| 6 | *Is your educational background in computer science or a related field?* | single_choice | "Yes", "No — different STEM field", "No — non-STEM field". |

#### Coding Background

| # | Question | Type | Options / Notes |
|---|----------|------|-----------------|
| 7 | *How many years have you been coding in total?* | number | Whole years. Following the [Stack Overflow Developer Survey](https://survey.stackoverflow.co/2025/) approach. |
| 8 | *How many years have you been coding in Python?* | number | Whole years. |
| 9 | *How many years of professional (paid) software development experience do you have?* | number | Whole years. 0 is valid (hobbyists, students). |
| 10 | *What industry do you work in?* | single_choice | "Software / Technology", "Finance / Fintech", "Healthcare / Biotech", "Education / Academia", "Government / Public sector", "E-commerce / Retail", "Gaming", "Consulting / Agency", "Startup (pre-revenue)", "Not currently employed in tech", "Other (please specify)". Important covariate — industry may influence coding style and AI adoption. |
| 11 | *What best describes your current role?* | single_choice | "Student", "Junior developer (0–2 years)", "Mid-level developer (3–5 years)", "Senior developer (6–10 years)", "Staff / Principal engineer (10+ years)", "Engineering manager / lead", "Data scientist / analyst", "Academic / researcher", "Hobbyist / side-project coder", "Other (please specify)". |
| 12 | *What other programming languages do you use regularly?* | multi_choice | "JavaScript/TypeScript", "Java", "C/C++", "C#", "Go", "Rust", "Ruby", "PHP", "R", "Swift", "Kotlin", "Other". Helps contextualise Python-specific skill. |
| 13 | *How would you rate your Python proficiency?* | scale | 1 (Beginner) – 7 (Expert). Subjective self-rating; interesting to compare against actual performance. |

#### Challenge Familiarity

| # | Question | Type | Options / Notes |
|---|----------|------|-----------------|
| 14 | *How familiar are you with LeetCode-style coding challenges?* | single_choice | "Very familiar — I practise regularly", "Somewhat familiar — I've done them before", "Vaguely aware — I know what they are but rarely do them", "Not familiar at all". Critical covariate — LeetCode grinders will score higher regardless of vibe-coding habits. |
| 15 | *Have you explicitly trained/practised with coding challenges (e.g. LeetCode, HackerRank, Codewars)?* | single_choice | "Yes — currently practising", "Yes — but not in the last 6 months", "Yes — but not in the last 1–2 years", "Yes — but it was over 2 years ago", "No — never". |
| 16 | *If you have practised, roughly how many problems have you completed in total?* | single_choice | "Fewer than 20", "20–50", "50–150", "150–300", "300+", "Not applicable". Helps distinguish casual from heavy LeetCode users. |

#### AI and Vibe Coding

| # | Question | Type | Options / Notes |
|---|----------|------|-----------------|
| 17 | *Do you currently use AI coding assistants (e.g. GitHub Copilot, Cursor, ChatGPT, Claude)?* | single_choice | "Yes — daily", "Yes — a few times a week", "Yes — occasionally", "No — I've tried them but stopped", "No — I've never used them". |
| 18 | *Which AI coding tools do you use?* | multi_choice | "GitHub Copilot", "Cursor", "ChatGPT", "Claude", "Gemini", "Codeium / Windsurf", "Amazon Q", "Other (please specify)". Shown conditionally if Q17 != never. |
| 19 | *When did you start using AI coding tools?* | single_choice | "Less than 3 months ago", "3–6 months ago", "6–12 months ago", "1–2 years ago", "2+ years ago". |
| 20 | *What percentage of your coding time is currently "vibe coding" (i.e. AI generates most of the code, you guide and review)?* | scale | 0%–100% slider. This is the key baseline measure — also asked per-session in the habit survey. |
| 21 | *What percentage of your coding time was "vibe coding" 12 months ago?* | scale | 0%–100% slider. Gives a retrospective sense of trajectory. |
| 22 | *On average, how many hours per week do you spend coding (all types)?* | number | Whole hours. |

#### Motivations and Context

| # | Question | Type | Options / Notes |
|---|----------|------|-----------------|
| 23 | *Why are you interested in this study?* | multi_choice | "I'm curious whether my own skills are changing", "I want to contribute to research", "I enjoy coding challenges", "My employer/university suggested it", "Other". Useful for understanding sampling bias. |
| 24 | *How did you hear about this study?* | single_choice | "Social media", "Hacker News / Reddit", "A colleague / friend", "University / employer", "News article", "Other". Helps track recruitment channels. |

### 8.4 Sensitivity and Inclusivity Notes
- **Gender question:** follows [Gallup's inclusive approach](https://news.gallup.com/opinion/methodology/505664/asking-inclusive-questions-gender-phase.aspx) — open-ended self-describe option, "prefer not to say" always available, question is **not marked as required**.
- **Age:** collected as a number rather than forced into bins, so we can use it as a continuous covariate. Reported publicly only in aggregate ranges. Question is **not marked as required**.
- **No questions about race/ethnicity at launch** — while relevant for equity research, it's not central to the vibe-coding hypothesis and risks being off-putting for a global, anonymous citizen-science study. Can be added later via the admin panel if the community and ethics board support it.
- **All questions clearly explain why they're asked** — the `help_text` field is used to show a brief rationale (e.g. *"This helps us understand whether coding experience affects skill trajectory."*).
- **"Prefer not to say" / skip option** on every sensitive question.

---

## 9. Data Model (Django)

### 9.1 Key Entities

```
Participant
  - user (FK -> Django User)
  - has_active_consent (bool, denormalised — True if latest ConsentRecord matches active ConsentDocument)
  - profile_completed (bool — True once intake questionnaire is finished)
  - profile_updated_at (datetime — last time any SurveyResponse was modified)

Session
  - participant (FK)
  - started_at (datetime)
  - completed_at (datetime)
  - challenges_attempted (int)
  - distraction_free (nullable bool — optional post-session self-report, see §4.2)

-- NOTE: CodingHabitSurvey is no longer a separate model.
-- Post-session habit questions (vibe coding %, hours/week, tools used, etc.)
-- are now SurveyQuestion entries with context="post_session", and responses
-- are SurveyResponse rows linked to the Session FK. See §8.2.

Challenge
  - external_id (e.g. Exercism slug, APPS problem ID)
  - title
  - description (markdown)
  - skeleton_code (the partial code shown to the participant)
  - test_cases (JSON -- list of input/expected-output pairs)
  - difficulty (Easy / Medium / Hard or numeric score)
  - tags (e.g. arrays, recursion, DP)

ChallengeAttempt
  - participant (FK)
  - challenge (FK)
  - session (FK)
  - submitted_code
  - tests_passed (int)
  - tests_total (int)
  - time_taken_seconds (float)       -- wall clock from display to submit
  - active_time_seconds (float)      -- wall clock minus idle periods
  - idle_time_seconds (float)        -- total time tab was unfocused or no keystrokes
  - started_at (datetime)
  - submitted_at (datetime)
  - skipped (bool)  -- participant saw it but chose not to attempt
  - think_aloud_active (bool)        -- was think-aloud recording on for this attempt?
```

### 9.2 Outcome Variables for Analysis
- **Accuracy:** `tests_passed / tests_total` per attempt.
- **Speed:** `time_taken_seconds`, possibly normalised by difficulty.
- **Composite score:** weighted combination of accuracy and speed.
- **Completion rate:** proportion of challenges attempted vs. presented in a session.

---

## 10. Statistical Analysis Design

### 10.1 Why Bayesian?

The flexible session structure produces **unbalanced data**: participants contribute different numbers of sessions, each with different numbers of challenges. Bayesian multilevel models handle this gracefully:

- **Partial pooling** — each participant's estimate is a weighted blend of their own data and the population average. Participants with fewer observations are pulled more toward the group mean, preventing noisy estimates from dominating. ([brms multilevel vignette](https://cran.r-project.org/web/packages/brms/vignettes/brms_multilevel.pdf))
- **No convergence failures** — unlike frequentist `lme4`, Bayesian models with weakly informative priors do not fail to converge on complex random-effects structures. ([Applied longitudinal data analysis in brms](https://bookdown.org/content/4253/))
- **Principled uncertainty** — posterior distributions give credible intervals rather than p-values, which is more interpretable for a citizen-science audience.

### 10.2 Model Specification

```
accuracy ~ vibe_coding_pct * months_since_baseline
           + hours_per_week
           + difficulty
           + (1 + months_since_baseline | participant)
           + (1 | challenge)
```

- **Random intercept + slope for participant:** captures individual baseline ability *and* individual rate of change over time.
- **Random intercept for challenge:** captures item-level difficulty beyond the fixed difficulty rating.
- **Key interaction:** `vibe_coding_pct * months_since_baseline` — does higher vibe-coding predict steeper skill decline (or improvement) over time?
- **Time-varying predictors:** `vibe_coding_pct` and `hours_per_week` can change from session to session, reflecting the participant's evolving habits.

### 10.3 Secondary Models
- **Speed model:** same structure but with `log(time_taken_seconds)` as outcome.
- **Item Response Theory (IRT):** fit a 2PL or 3PL model to estimate latent ability per participant per time point, then use ability estimates as the outcome in the longitudinal model.

### 10.4 Tools
- **R:** [`brms`](https://paul-buerkner.github.io/brms/) (front-end to Stan) — the primary analysis tool. Comprehensive tutorials exist for exactly this type of [longitudinal multilevel Bayesian analysis](https://www.andreashandel.com/posts/2022-02-22-longitudinal-multilevel-bayes-1/).
- **Python alternative:** `bambi` (PyMC-based) if we prefer to stay in the Python ecosystem.
- Analysis scripts kept in a separate `analysis/` directory in this repo.

### 10.5 Power / Sample Considerations
- Target >= 200 participants with >= 3 time points each over 12+ months.
- Even with unbalanced data, Bayesian partial pooling extracts information efficiently from participants with fewer sessions.
- Simulation-based power analysis (using `brms` or `simr`) to confirm sensitivity before launch.

---

## 11. Citizen Science Approach

### 11.1 Philosophy
This is not a top-down study with passive subjects — it is a **participatory, citizen-science project** where the coding community actively contributes to understanding the effects of AI on their own skills. Participants are collaborators, not just data sources.

### 11.2 Community Input on Study Design

Community discussion and study design input are handled via **external services** — not built into the app. This keeps the app focused and leverages platforms the developer audience already uses.

#### GitHub Discussions — the structured record
- **Primary channel** for study design input: proposals, feature requests, survey question suggestions, analysis ideas, bug reports.
- Organised into categories: "Study Design", "Challenge Suggestions", "Analysis Ideas", "General Q&A".
- Threaded and searchable — decisions don't get lost in chat history.
- Supports upvoting, so the community can signal which ideas have the most support.
- Linked from the app's footer and the "Get Involved" page.
- Lives alongside the open-source repo, so technical contributors can move seamlessly between discussion and code.

#### Discord — the community watercooler
- **Secondary channel** for casual conversation, quick questions, real-time chat, and community bonding.
- Channels: `#general`, `#study-design`, `#challenge-ideas`, `#show-your-results`, `#off-topic`.
- Announcements channel (read-only) for study updates, new challenge drops, and milestone celebrations.
- Low barrier — easy to join, encourages ongoing engagement between monthly sessions.
- **Not the record of decisions** — if a Discord conversation leads to a study design change, it gets written up as a GitHub Discussion for the formal record.

#### Periodic Design Votes
- For non-critical design decisions (e.g. "should we add a new challenge category?"), post a poll on GitHub Discussions with a 1–2 week voting window.
- Discord polls for quick-pulse informal opinions.
- Results summarised and published transparently.

#### Transparent Changelog
- Every change to the study protocol is logged publicly (in the repo and announced on Discord) so the community can see how their input shaped the study.
- Follow [best practices for participatory science](https://theoryandpractice.citizenscienceassociation.org/articles/10.5334/cstp.227) including transparent data management and ethical oversight.

### 11.3 Giving Back to Participants

#### Personal Dashboard (available immediately)
- **Performance over time:** line charts showing accuracy and speed trends across sessions.
- **Difficulty breakdown:** how the participant performs on Easy / Medium / Hard challenges.
- **Comparison to cohort:** anonymised percentile bands (e.g. "you scored in the top 30% this month") without revealing individual data.
- **Habit tracking:** graphs of self-reported vibe-coding percentage and hours per week over time, overlaid with performance trends so the participant can see their own relationship between habits and skill.

#### Community-Wide Insights (front page, available to all visitors)
- **Live aggregate trend graphs** on the landing page showing:
  - Average accuracy over time across all participants.
  - Performance trends split by vibe-coding intensity (low / medium / high).
  - Participation growth (number of active participants per month).
- These graphs update automatically and serve as both a recruitment tool and a transparency measure.
- No individual-level data is exposed in public graphs — only aggregates with sufficient group sizes (n >= 10 per bin).

---

## 12. Open Data Policy

### 12.1 Principles
- All data collected is intended to be **openly available** for analysis by anyone.
- Data is fully **anonymised** — no usernames, emails, or any identifying information in the public dataset.
- Each participant is represented by a random, opaque ID.

### 12.2 Access Model

| Who | What they see | When |
|-----|---------------|------|
| **Any visitor** (no login) | Aggregate trend graphs on front page | Immediately |
| **Participants** (logged in) | Their own personal data + aggregate graphs | Immediately |
| **Participants** (logged in) | Full anonymised dataset (all participants) | After 12-month embargo |
| **Researchers** (upon request) | Early access to anonymised dataset for peer-reviewed research | Case-by-case, with ethical review |

### 12.3 The 12-Month Embargo
- The full anonymised dataset is released **one year after the first data collection begins**.
- This embargo period allows the study to accumulate sufficient data before public release, avoiding premature conclusions from small samples.
- After the embargo, the dataset updates periodically (e.g. quarterly).
- Participants are informed about this timeline at registration.

### 12.4 Data Format
- Published as downloadable CSV / Parquet files.
- Accompanied by a data dictionary and codebook.
- Consider using [PPSR Core](https://citizens-guide-open-data.github.io/guide/6-citizen-science) metadata standards for interoperability with other citizen-science platforms.

---

## 13. Participant Results and Visualisations

### 13.1 Personal Results (rich, interactive)
Participants deserve more than a score — they get a **personal research dashboard**:

- **Skill trajectory chart:** accuracy (y-axis) over time (x-axis), with confidence bands. Each session is a data point.
- **Speed trajectory chart:** same format, showing whether they're getting faster or slower.
- **Difficulty radar chart:** performance broken down by challenge tags (arrays, recursion, DP, etc.).
- **Habit overlay:** optional toggle to overlay their self-reported vibe-coding % on the same time axis as their skill charts, so they can visually inspect the relationship.
- **Session summary cards:** for each past session, a summary showing challenges attempted, accuracy, time spent, and how it compares to their own average.

### 13.2 Front-Page Public Graphs
The landing page showcases the study's emerging findings to attract participants and demonstrate transparency:

- **"The Big Question" chart:** average skill trajectory for high vs. low vibe-coders over time.
- **Participation map:** total sessions completed, active participants, challenges solved.
- **Monthly snapshot:** headline stats updated each month.
- All rendered with a charting library (e.g. Chart.js, Plotly.js, or D3) — interactive and mobile-friendly.

### 13.3 Call for Collaborators
A prominent section on the landing page actively recruiting collaborators:

- **"Help us answer The Big Question"** — a clear call-to-action for researchers, data scientists, and developers who want to contribute to the study.
- Roles we're looking for: co-investigators, statisticians, front-end contributors, challenge authors, translators, outreach help.
- Link to a **collaborator interest form** (simple: name, affiliation, how they'd like to help) — submissions stored in the database and reviewed by admins.
- Link to the project's open-source repo (GitHub) for technical contributors.

### 13.4 Sponsors and Support
A "Supported by" / "Sponsored by" section on the landing page:

- **Logo grid** for current sponsors/supporters (universities, companies, foundations).
- **"Become a sponsor"** link leading to a page explaining:
  - What the project is and why it matters.
  - What sponsorship funds (hosting, STT transcription costs, researcher time, participant incentives).
  - Sponsorship tiers (if applicable) or simply a contact form.
- **"Get in touch"** — a general contact link/form for press, partnership enquiries, or ethics questions.
- Sponsor logos and details are **admin-managed** (a simple `Sponsor` model with name, logo, URL, tier, display order) so they can be added/removed without code changes.

---

## 14. Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Backend | **Django** (Python) | Project guidelines mandate Django; handles auth, API, data storage. |
| Database | **PostgreSQL** | Robust for relational data with JSON fields. |
| Frontend | **Django templates + vanilla JS** (initially) | Keep it simple; Pyodide integration is JS-based. |
| In-browser Python | **Pyodide** (precompiled WASM) | No server-side code execution needed. |
| Charts | **Plotly.js** or **Chart.js** | Interactive, responsive graphs for participant dashboards and front page. |
| Background tasks | **Huey** | Per project guidelines (no Celery). |
| Analysis | **R + brms** (primary), **Python + bambi** (secondary) | Bayesian multilevel modelling. |
| Deployment | **Hetzner** VPS, managed via **Appliku** | Cost-effective EU-based hosting; Appliku handles Docker deployment, SSL, and scaling. |

---

## 15. Accessibility

As a public citizen-science project, accessibility is both an ethical requirement and important for sample diversity — excluding participants with disabilities biases the dataset.

### 15.1 Standards
- Target **WCAG 2.1 AA** compliance across all pages.
- Use semantic HTML throughout (`<main>`, `<nav>`, `<label>`, `<fieldset>`, etc.).

### 15.2 Code Editor
- The code editor (likely CodeMirror or Monaco) must support **full keyboard navigation** — no mouse-only interactions.
- Ensure `aria-label` attributes on the editor, run/submit buttons, and test output areas.
- Screen reader users should be able to hear challenge descriptions, their code, and test results.

### 15.3 Charts and Visualisations
- All charts use a **colourblind-friendly palette** (e.g. Okabe-Ito or viridis) — no red/green distinctions.
- Every chart includes a **text summary** or data table alternative so the information is accessible without vision.
- Interactive chart elements are keyboard-focusable with visible focus indicators.

### 15.4 Forms and Surveys
- All form fields have associated `<label>` elements.
- Error messages are linked to their fields via `aria-describedby`.
- Likert scales / sliders are operable via keyboard (arrow keys).

### 15.5 General
- Minimum contrast ratio of 4.5:1 for text, 3:1 for large text and UI components.
- No information conveyed by colour alone.
- Responsive design that works at 200% zoom without horizontal scrolling.
- Skip-to-content link on every page.

---

## 16. MVP Scope (Phase 1)

1. User registration and login.
2. Informed consent gate (§7) — versioned consent document, explicit consent record.
3. Participant intake questionnaire (§8) — all 24 default questions via the unified question system.
4. Unified question system (§8.2) — single `SurveyQuestion`/`SurveyResponse` model powering profile, post-challenge, and post-session questions, all admin-configurable.
5. A curated set of ~50 challenges across all 5 tiers (~15 Tier 1, ~15 Tier 2, ~10 Tier 3, ~5 Tier 4, ~5 Tier 5).
6. Assessment session: present challenges one at a time in ascending difficulty (up to 10), participant decides when to stop.
7. Session frequency enforcement (minimum 28 days between sessions).
8. Post-challenge reflection questions and post-session habit survey (both via unified question system).
9. Basic personal results page (accuracy and speed over sessions).
10. Front-page aggregate graphs (even with small N, show participation stats and early trends).
11. Basic admin dashboard showing participation stats and question management.
12. Automated monthly reminder emails (Huey tasks) — opt-in, sent if no session in the past month.

---

## 17. Future Phases

- **Phase 2:** Expand challenge pool to 100+. Add adaptive difficulty selection. Rich personal dashboard with all visualisation features described in §13. Community feedback mechanism.
- **Phase 3:** Full open-data portal with downloadable anonymised dataset (after 12-month embargo). Analysis scripts published in `analysis/` directory.
- **Phase 4:** Community discussion forum for citizen-science input. Gamification (streaks, badges) to improve retention. Integration with GitHub activity data (with consent) as an objective coding-volume measure.
- **Phase 5:** Pre-registered analysis plan. First formal publication of results. Invite external researchers to collaborate on analyses using the open dataset.

---

## 18. Ethical Considerations

- **Informed consent is enforced in-app** — see §7 for the full consent system. No participation without an explicit, versioned consent record stored in the database.
- Data stored pseudonymously (no real names required beyond login).
- Participants can withdraw and request data deletion at any time via profile settings. Withdrawal is timestamped in the database. Already-released anonymised snapshots cannot be recalled, but future releases will exclude withdrawn participants.
- **Consent documents are admin-editable** — corrections or updates to the consent text can be made at any time. Participants are re-consented to new versions before continuing.
- Optional elements (think-aloud audio, transcript sharing, reminder emails) have **separate opt-in consent records**.
- **Ethics approval will be obtained from Royal Holloway, University of London** (lead researcher's institution). The consent audit log (§7.4) and exportable consent records support ethics board reporting and any conditions imposed during review.
- GDPR compliance for EU participants.
- Follow [ethical citizen-science data management guidelines](https://theoryandpractice.citizenscienceassociation.org/articles/10.5334/cstp.538).
- Transparent about study limitations — self-report measures of vibe-coding are inherently noisy; emphasise this in any publications.
