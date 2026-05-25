# Analysis: AI Usage vs Session Outcomes (Cross-Sectional)

**Date:** 2026-05-24  
**Analyst:** Andy T Woods (via Claude Code / claude-sonnet-4-6)  
**Data source:** Production DB — `config.settings.remote_on_local`  
**Blog post:** [Early Signals: AI Usage and Coding Performance](/blog/2026-05-24-early-ai-usage-signals/)

---

## Scope

Cross-sectional correlation between self-reported AI usage (% of code AI-generated) and three session-level outcome variables:

- **Accuracy** — average `tests_passed / tests_total` per non-skipped challenge (%)
- **Completion rate** — % of non-skipped attempts where all tests passed
- **Speed** — average `active_time_seconds` per non-skipped challenge (seconds where keystrokes occurred, not raw wall-clock)

## Filters Applied

- `CodeSession.is_mock = False` — excludes developer test sessions
- `CodeSession.status = 'completed'` — completed sessions only
- `ChallengeAttempt.skipped = False` — excludes skipped challenges
- `ChallengeAttempt.tests_total > 0` — excludes attempts with no test cases

## AI Usage Variable

Primary: `SurveyResponse` for question id=43 (post-session, context=`post_session`):
> *"In the past month, roughly what percentage of the code you wrote was AI-generated?"*

Fallback: `SurveyResponse` for question id=46 (profile intake, context=`profile`):
> *"In a typical coding session, roughly what percentage of your final code is AI-generated?"*

Sessions without either response were excluded (0 excluded in this run).

## Queries

Run via `manage.py shell -c` with `DJANGO_SETTINGS_MODULE=config.settings.remote_on_local`.

```python
from agenticbrainrot.surveys.models import SurveyResponse
from agenticbrainrot.challenges.models import ChallengeAttempt
from agenticbrainrot.coding_sessions.models import CodeSession
from django.db.models import Avg, F, Q, Count

# AI usage per session (post-session survey)
session_ai_pct = {
    r.session_id: float(r.value)
    for r in SurveyResponse.objects.filter(question_id=43)
    if r.value.replace('.','',1).isdigit()
}

# AI usage per participant (profile fallback)
ai_pct_by_p = {}
for r in SurveyResponse.objects.filter(question_id=46).order_by('answered_at'):
    try:
        ai_pct_by_p[r.participant_id] = float(r.value)
    except (ValueError, TypeError):
        pass

# Per-session outcomes
for sess in CodeSession.objects.filter(is_mock=False, status='completed'):
    attempts = ChallengeAttempt.objects.filter(session=sess, skipped=False, tests_total__gt=0)
    agg = attempts.aggregate(
        avg_acc=Avg(F('tests_passed') * 100.0 / F('tests_total')),
        avg_time=Avg('time_taken_seconds'),
        n=Count('id'),
        passed=Count('id', filter=Q(tests_passed=F('tests_total'))),
    )
    ai = session_ai_pct.get(sess.id) or ai_pct_by_p.get(sess.participant_id)
    # ...
```

## Results

### Sample

- Completed non-mock sessions with outcome data: **19**
- Participants represented: **19**
- Sessions excluded (no AI% data): **0**
- Sessions excluded (zero challenges passed – failed engagement): **1**

### Pearson Correlations (AI% vs outcome)

| Outcome | r | n |
|---|---|---|
| Accuracy | +0.389 | 19 |
| Completion rate | +0.134 | 19 |
| Active time/challenge | +0.232 | 19 |

Note: with n=20, 95% CI on r=0.477 is approximately [0.05, 0.74]. These estimates carry substantial uncertainty.

### Group Breakdown

| Group | AI% range | n sessions | Avg accuracy | Avg completion rate | Avg time (s) |
|---|---|---|---|---|---|
| Low | ≤25% | 4 | 61.9% | 54.4% | 110.0 |
| Mid | 26–75% | 10 | 94.8% | 86.6% | 126.7 |
| High | >75% | 6 | 99.5% | 97.2% | 168.5 |

### Raw Session Data

See `data.json` for full per-session values and anonymous participant-level data (programming years, Python years, AI usage %). Sessions are identified by an anonymous row number (1–20) ordered by internal session ID; no database identifiers are included in the public file.

## Reproducing the Analysis

All statistics in the blog post can be reproduced from `data.json` alone using the bundled script (standard library only, no dependencies):

```bash
python analyse.py
```

The script fetches `data.json` from GitHub automatically if not found locally.

## Key Caveats

1. **Cross-sectional only.** No within-person longitudinal variation yet — nearly all participants have a single session.
2. **Almost certainly confounded.** More experienced developers likely adopted AI tools earlier and also score higher on challenges. AI usage and ability share a common cause (experience). No causal inference is possible from this snapshot.
3. **Self-report noise.** AI% is a rough estimate, not an instrumented measure.
4. **No difficulty control.** Challenges are randomly assigned; sessions are not matched on difficulty.
5. **Tiny N.** 20 sessions. All correlations should be treated as exploratory.

## What to Watch

- The `accuracy ~ vibe_coding_pct × months_since_baseline` interaction (the primary study hypothesis) requires multiple sessions per participant.
- The positive speed correlation (high AI users are slower but more accurate) is the most unexpected finding; worth tracking.

## Efficiency Ratio Methodology

The efficiency ratio is computed **client-side in the browser** using [Pyodide](https://pyodide.org/) — CPython compiled to WebAssembly, running inside a dedicated Web Worker. No participant code is executed on the server.

### Computation steps

1. After a participant submits their solution and all test cases pass, the web worker runs a timing routine.
2. The participant's function and the challenge's `reference_solution` are each timed using `time.monotonic()` inside Pyodide.
3. Each solution is called repeatedly in a tight loop with the same test-case inputs, for up to 2 seconds or 15 collected samples (whichever comes first).
4. The **median** of collected per-call timings (in microseconds) is used for each solution to reduce variance from JIT warm-up and garbage collection.
5. `efficiency_ratio = participant_median_µs / reference_median_µs` — rounded to 2 decimal places.
6. Only this ratio (a single float) is sent to the server via the challenge submission POST request.

### Edge cases

- **Class-based or stateful challenges** are skipped (ratio recorded as `null`); only standard function-call test cases are timed.
- If either solution times out or throws during timing (not during testing), ratio is `null`.
- A ratio of exactly `1.0` is recorded when the reference runtime is zero (degenerate case).

### Reference solutions

For benchmark fixtures (MBPP, HumanEval), the reference solution is drawn directly from the published dataset and stored in `Challenge.reference_solution`. Screening fixtures have researcher-written reference solutions. In both cases the reference is the same for every participant attempting that challenge, so comparisons are fair within-challenge.

### Interpretation

| Ratio | Meaning |
|---|---|
| < 1.0 | Participant code runs faster than the reference |
| 1.0 | Matched |
| > 1.0 | Participant code runs slower (e.g. 2.0 = twice as slow) |

A ratio > 1 does not imply "wrong" — many valid solutions are less optimised than the canonical answer. The ratio is a measure of computational efficiency, not correctness (correctness is determined by whether all tests pass).
