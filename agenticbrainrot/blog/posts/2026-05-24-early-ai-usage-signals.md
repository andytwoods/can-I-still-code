---
title: Early Signals: AI Usage and Coding Performance
date: 2026-05-24
author: Andy T Woods
summary: High AI users outperform low AI users in our first 20 sessions. That sounds like the wrong result — and it's exactly why longitudinal design matters. A cross-sectional snapshot can't separate skill from selection bias; only within-person tracking over time can.
analysis_ref: 2026-05-24-ai-usage-correlation
---

## 20 sessions in. Here's what the data looks like — and why you shouldn't read too much into it yet.

This study is built around one core question: does heavy use of AI coding tools affect your ability to write code without them? We're not going to answer that today. But we do have enough early data to run a first sanity check — and the early data already illustrates perfectly why the study is designed the way it is.

All numbers in this post are reproducible from the [analysis log](https://github.com/andytwoods/agenticbrainrot/tree/master/analysis/2026-05-24-ai-usage-correlation).

---

## Why longitudinal design matters — and why this data shows it

The headline finding from our first 20 sessions is that higher self-reported AI usage correlates *positively* with coding accuracy (r = +0.48). In other words: the more AI a participant uses day-to-day, the better they tend to perform on our challenges.

If you came here expecting to see evidence that AI is rotting people's coding skills, that looks like the opposite of what you'd predict.

But here is the problem: **we are only observing each person at a single point in time.** We cannot yet tell whether a high-AI user is performing well *because* of their AI habits, *despite* them, or — most likely — because they were already a stronger programmer before AI tools even entered the picture. More experienced developers adopted AI coding tools earlier and more heavily. Those same developers also perform better on coding challenges. Both things are downstream of programming experience; AI usage may be doing no causal work at all.

This is the textbook case for why cross-sectional data cannot answer causal questions about skill change. When you compare people to each other at a single timepoint, you are measuring *who they already are*, not *what is happening to them*. The only way to separate the effect of AI tool use from pre-existing ability is to track the **same person over time** — watching whether their performance rises or falls as their AI habits change. That is exactly what this study is designed to do.

Right now we have 19 participants with exactly one completed session. That is not enough longitudinal data to say anything about the main hypothesis. What we can do is show you the cross-sectional picture in full, flag where it is and isn't trustworthy, and set up the baseline for what comes next.

---

---

## What We Have

As of May 2026 we have **20 completed sessions** from **19 participants**. Each session involves solving Python challenges without AI assistance, followed by a short post-session survey. That survey includes the key question:

> *In the past month, roughly what percentage of the code you wrote was AI-generated?*

We also collect the same question on signup (profile intake) and use it as a fallback when the post-session answer is missing.

### The Four Outcome Variables

For each session we compute four numbers — all excluding skipped challenges:

| Variable | Definition |
|---|---|
| **Accuracy** | Average `tests_passed / tests_total` across challenges, expressed as a % |
| **Completion rate** | % of attempted challenges where *all* test cases passed |
| **Speed** | Average wall-clock time in seconds per challenge |
| **Efficiency ratio** | Participant solution runtime ÷ reference solution runtime. 1.0 = matched canonical; >1 = slower-running code |

The first three map directly to the primary outcomes in the [study design](/about): accuracy, speed, and completion as a proxy for overall success. Efficiency ratio is a secondary measure of code quality — whether participants write solutions that run fast, not just solutions that pass.

---

## What We Found

<div class="notification is-warning is-light">
<strong>Important caveat before the charts:</strong> this is a cross-sectional snapshot of 20 sessions, mostly single observations per person. The correlations tell us about the relationship between AI usage and <em>current</em> performance — they say nothing about how performance <em>changes over time</em> as AI usage changes. That question requires longitudinal data, which we don't have yet.
</div>

### Correlations with AI Usage

Simple Pearson correlations between reported AI usage percentage and each outcome:

| Outcome | r | n | Rough interpretation |
|---|---|---|---|
| Accuracy | **+0.48** | 20 | Moderate positive |
| Completion rate | **+0.32** | 20 | Weak-to-moderate positive |
| Time per challenge | **+0.31** | 20 | Weak positive |
| Efficiency ratio | **–0.10** | 19 | Negligible |

Higher self-reported AI usage correlates positively with all three outcomes. On its face this looks like "AI users are better coders." We'll come back to why that's almost certainly the wrong interpretation.

### Performance by AI Usage Group

Splitting sessions into three bands by reported AI usage:

<div class="chart-wrap">
  <canvas id="chart-groups" style="max-height:380px"></canvas>
</div>

<script>
(function () {
  function init() {
    new Chart(document.getElementById('chart-groups'), {
      type: 'bar',
      data: {
        labels: ['Low (≤25% AI, n=4)', 'Mid (26–75%, n=10)', 'High (>75% AI, n=6)'],
        datasets: [
          {
            label: 'Accuracy %',
            data: [61.9, 94.8, 99.5],
            backgroundColor: 'rgba(0, 114, 178, 0.85)',
            borderColor: 'rgb(0, 114, 178)',
            borderWidth: 1,
          },
          {
            label: 'Completion rate %',
            data: [54.4, 86.6, 97.2],
            backgroundColor: 'rgba(0, 158, 115, 0.85)',
            borderColor: 'rgb(0, 158, 115)',
            borderWidth: 1,
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'top' },
          title: { display: true, text: 'Performance by AI Usage Group (n=20 sessions)' }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 115,
            ticks: { callback: function(v) { return v + '%'; } },
            title: { display: true, text: 'Score (%)' }
          },
          x: { title: { display: true, text: 'Self-reported AI usage (% of code AI-generated)' } }
        }
      }
    });
  }
  whenInView('chart-groups', init);
})();
</script>

The gap between the low and high groups is striking — accuracy jumps from 62% to 99.5%. But notice the sample sizes in the labels: 4, 10, and 6 sessions. The low-AI group average is pulled down by one session where a participant passed zero challenges (see the raw data in the [analysis log](https://github.com/andytwoods/agenticbrainrot/tree/master/analysis/2026-05-24-ai-usage-correlation)).

### AI Usage vs Accuracy (per session)

Each bubble below is one session. Bubble size is proportional to the number of challenges attempted.

<div class="chart-wrap">
  <canvas id="chart-scatter-accuracy" style="max-height:420px"></canvas>
</div>

<script>
(function () {
  function linReg(pts) {
    var n = pts.length, sx = 0, sy = 0, sxy = 0, sxx = 0;
    pts.forEach(function(p) { sx += p.x; sy += p.y; sxy += p.x * p.y; sxx += p.x * p.x; });
    var slope = (n * sxy - sx * sy) / (n * sxx - sx * sx);
    var intercept = (sy - slope * sx) / n;
    return [{x: 0, y: intercept}, {x: 100, y: slope * 100 + intercept}];
  }
  function init() {
    var ctx = document.getElementById('chart-scatter-accuracy');
    if (!ctx) return;
    var OUTLIER_IDX = 0;
    var defaultBg = 'rgba(0, 114, 178, 0.55)';
    var defaultBorder = 'rgba(0, 114, 178, 0.9)';
    var outlierBg = 'rgba(213, 94, 0, 0.7)';
    var outlierBorder = 'rgba(213, 94, 0, 1)';
    var bubbles = [
      {x: 0,  y: 0.0,  r: 4,  n: 1},
      {x: 0,  y: 77.8, r: 7,  n: 6},
      {x: 0,  y: 73.3, r: 7,  n: 5},
      {x: 0,  y: 96.4, r: 10, n: 11},
      {x: 30, y: 100,  r: 7,  n: 5},
      {x: 30, y: 100,  r: 4,  n: 1},
      {x: 33, y: 100,  r: 6,  n: 4},
      {x: 50, y: 98.2, r: 10, n: 11},
      {x: 50, y: 100,  r: 5,  n: 2},
      {x: 50, y: 100,  r: 5,  n: 3},
      {x: 50, y: 100,  r: 8,  n: 7},
      {x: 50, y: 75.0, r: 6,  n: 4},
      {x: 75, y: 75.0, r: 4,  n: 1},
      {x: 75, y: 100,  r: 7,  n: 6},
      {x: 85, y: 100,  r: 4,  n: 1},
      {x: 90, y: 100,  r: 10, n: 10},
      {x: 90, y: 100,  r: 4,  n: 1},
      {x: 90, y: 100,  r: 6,  n: 4},
      {x: 95, y: 100,  r: 4,  n: 1},
      {x: 95, y: 96.7, r: 10, n: 12}
    ];
    var bgColors = bubbles.map(function(_, i) { return i === OUTLIER_IDX ? outlierBg : defaultBg; });
    var borderColors = bubbles.map(function(_, i) { return i === OUTLIER_IDX ? outlierBorder : defaultBorder; });
    new Chart(ctx, {
      type: 'bubble',
      data: {
        datasets: [
          {
            label: 'Session',
            data: bubbles,
            backgroundColor: bgColors,
            borderColor: borderColors,
            borderWidth: 1,
          },
          {
            type: 'line',
            label: 'Trend',
            data: linReg(bubbles),
            borderColor: 'rgba(0, 114, 178, 0.5)',
            borderWidth: 1.5,
            borderDash: [6, 4],
            pointRadius: 0,
            fill: false,
            tension: 0,
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          title: { display: true, text: 'AI Usage % vs Challenge Accuracy (bubble size = challenges attempted)' },
          tooltip: {
            filter: function(item) { return item.datasetIndex === 0; },
            callbacks: {
              label: function(c) {
                var base = 'AI: ' + c.raw.x + '%  |  Accuracy: ' + c.raw.y + '%  |  n=' + c.raw.n;
                return c.dataIndex === OUTLIER_IDX ? base + '  ⚑ outlier' : base;
              }
            }
          }
        },
        scales: {
          x: { min: -5, max: 105, title: { display: true, text: 'Self-reported AI usage (% of code AI-generated)' } },
          y: { min: -5, max: 110, title: { display: true, text: 'Average accuracy %' } }
        }
      }
    });
  }
  whenInView('chart-scatter-accuracy', init);
})();
</script>

Notice the wide spread at AI% = 0. Some low-AI participants performed very well (96.4% accuracy over 11 challenges), others poorly. The red point is a notable outlier: a zero-AI participant who passed zero challenges in a single-attempt session — the only 0% accuracy result in the dataset. This single session pulls the low-AI group mean down considerably and inflates the positive correlation with AI usage. At high AI usage, sessions cluster near 100% accuracy with almost no variance. Whether that reflects genuine ability or something else is the question the longitudinal data will answer.

### The Speed Paradox

Here's the finding we find most interesting. If AI dependency were degrading hand-coding ability, you might expect high-AI users to take longer — grinding without their usual crutch. And indeed they do take longer. But they're *also* more accurate. So what's going on?

<div class="chart-wrap">
  <canvas id="chart-scatter-speed" style="max-height:420px"></canvas>
</div>

<script>
(function () {
  function linReg(pts) {
    var n = pts.length, sx = 0, sy = 0, sxy = 0, sxx = 0;
    pts.forEach(function(p) { sx += p.x; sy += p.y; sxy += p.x * p.y; sxx += p.x * p.x; });
    var slope = (n * sxy - sx * sy) / (n * sxx - sx * sx);
    var intercept = (sy - slope * sx) / n;
    return [{x: 0, y: intercept}, {x: 100, y: slope * 100 + intercept}];
  }
  function init() {
    var ctx = document.getElementById('chart-scatter-speed');
    if (!ctx) return;
    var bubbles = [
      {x: 0,  y: 81.0,  r: 4,  n: 1},
      {x: 0,  y: 77.5,  r: 7,  n: 6},
      {x: 0,  y: 88.4,  r: 7,  n: 5},
      {x: 0,  y: 202.5, r: 10, n: 11},
      {x: 30, y: 124.4, r: 7,  n: 5},
      {x: 30, y: 114.0, r: 4,  n: 1},
      {x: 33, y: 103.8, r: 6,  n: 4},
      {x: 50, y: 230.6, r: 10, n: 11},
      {x: 50, y: 136.5, r: 5,  n: 2},
      {x: 50, y: 292.0, r: 5,  n: 3},
      {x: 50, y: 63.6,  r: 8,  n: 7},
      {x: 50, y: 37.5,  r: 6,  n: 4},
      {x: 75, y: 128.0, r: 4,  n: 1},
      {x: 75, y: 116.3, r: 7,  n: 6},
      {x: 85, y: 168.0, r: 4,  n: 1},
      {x: 90, y: 238.1, r: 10, n: 10},
      {x: 90, y: 66.0,  r: 4,  n: 1},
      {x: 90, y: 33.8,  r: 6,  n: 4},
      {x: 95, y: 369.0, r: 4,  n: 1},
      {x: 95, y: 223.8, r: 10, n: 12}
    ];
    new Chart(ctx, {
      type: 'bubble',
      data: {
        datasets: [
          {
            label: 'Session',
            data: bubbles,
            backgroundColor: 'rgba(230, 159, 0, 0.55)',
            borderColor: 'rgba(230, 159, 0, 0.9)',
            borderWidth: 1,
          },
          {
            type: 'line',
            label: 'Trend',
            data: linReg(bubbles),
            borderColor: 'rgba(230, 159, 0, 0.5)',
            borderWidth: 1.5,
            borderDash: [6, 4],
            pointRadius: 0,
            fill: false,
            tension: 0,
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          title: { display: true, text: 'AI Usage % vs Time per Challenge (bubble size = challenges attempted)' },
          tooltip: {
            filter: function(item) { return item.datasetIndex === 0; },
            callbacks: {
              label: function(c) {
                return 'AI: ' + c.raw.x + '%  |  ' + c.raw.y + 's per challenge  |  n=' + c.raw.n;
              }
            }
          }
        },
        scales: {
          x: { min: -5, max: 105, title: { display: true, text: 'Self-reported AI usage (% of code AI-generated)' } },
          y: { min: 0, title: { display: true, text: 'Average seconds per challenge' } }
        }
      }
    });
  }
  whenInView('chart-scatter-speed', init);
})();
</script>

High AI users (>75%) average **183 seconds** per challenge versus 112 seconds for low AI users — they're slower *and* more accurate. Two hypotheses worth tracking as data accumulates:

1. **Heavy AI users tackle harder challenges more persistently** — instead of giving up quickly, they grind through. We can check this against challenge difficulty tier data once we have more sessions.
2. **Pacing habits transferred from AI-assisted work** — people used to iterating with AI feedback may naturally take more time verifying their solutions manually, even though they're ultimately right.

### Code Efficiency: A Null Result Worth Noting

One variable we track but hadn't included in this snapshot is the **efficiency ratio** — how fast a participant's submitted solution runs compared to a canonical reference solution (1.0 = matched; >1 = slower-running code). Coverage is high: 94 of 96 non-skipped attempts have an efficiency ratio (98%).

<div class="chart-wrap">
  <canvas id="chart-scatter-efficiency" style="max-height:420px"></canvas>
</div>

<script>
(function () {
  function linReg(pts) {
    var n = pts.length, sx = 0, sy = 0, sxy = 0, sxx = 0;
    pts.forEach(function(p) { sx += p.x; sy += p.y; sxy += p.x * p.y; sxx += p.x * p.x; });
    var slope = (n * sxy - sx * sy) / (n * sxx - sx * sx);
    var intercept = (sy - slope * sx) / n;
    return [{x: 0, y: intercept}, {x: 100, y: slope * 100 + intercept}];
  }
  function init() {
    var ctx = document.getElementById('chart-scatter-efficiency');
    if (!ctx) return;
    var OUTLIER_IDX = 0;
    var defaultBg = 'rgba(86, 180, 233, 0.55)';
    var defaultBorder = 'rgba(86, 180, 233, 0.9)';
    var outlierBg = 'rgba(213, 94, 0, 0.7)';
    var outlierBorder = 'rgba(213, 94, 0, 1)';
    var bubbles = [
      {x: 0,  y: 2.055, r: 10, n: 11},
      {x: 0,  y: 1.028, r: 7,  n: 6},
      {x: 0,  y: 1.02,  r: 6,  n: 5},
      {x: 30, y: 1.0,   r: 4,  n: 1},
      {x: 30, y: 0.802, r: 6,  n: 5},
      {x: 33, y: 0.938, r: 6,  n: 4},
      {x: 50, y: 1.018, r: 10, n: 11},
      {x: 50, y: 0.941, r: 7,  n: 7},
      {x: 50, y: 1.033, r: 5,  n: 3},
      {x: 50, y: 1.025, r: 5,  n: 2},
      {x: 50, y: 0.665, r: 6,  n: 4},
      {x: 75, y: 1.327, r: 7,  n: 6},
      {x: 75, y: 1.01,  r: 4,  n: 1},
      {x: 85, y: 1.27,  r: 4,  n: 1},
      {x: 90, y: 1.346, r: 10, n: 10},
      {x: 90, y: 0.687, r: 6,  n: 4},
      {x: 90, y: 1.32,  r: 4,  n: 1},
      {x: 95, y: 1.332, r: 10, n: 12},
      {x: 95, y: 0.84,  r: 4,  n: 1}
    ];
    var bgColors = bubbles.map(function(_, i) { return i === OUTLIER_IDX ? outlierBg : defaultBg; });
    var borderColors = bubbles.map(function(_, i) { return i === OUTLIER_IDX ? outlierBorder : defaultBorder; });
    new Chart(ctx, {
      type: 'bubble',
      data: {
        datasets: [
          {
            label: 'Session',
            data: bubbles,
            backgroundColor: bgColors,
            borderColor: borderColors,
            borderWidth: 1,
          },
          {
            type: 'line',
            label: 'Trend',
            data: linReg(bubbles),
            borderColor: 'rgba(86, 180, 233, 0.5)',
            borderWidth: 1.5,
            borderDash: [6, 4],
            pointRadius: 0,
            fill: false,
            tension: 0,
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          title: { display: true, text: 'AI Usage % vs Code Efficiency Ratio (bubble size = challenges attempted)' },
          tooltip: {
            filter: function(item) { return item.datasetIndex === 0; },
            callbacks: {
              label: function(c) {
                var base = 'AI: ' + c.raw.x + '%  |  efficiency: ' + c.raw.y + '×  |  n=' + c.raw.n;
                return c.dataIndex === OUTLIER_IDX ? base + '  ⚑ outlier' : base;
              }
            }
          }
        },
        scales: {
          x: { min: -5, max: 105, title: { display: true, text: 'Self-reported AI usage (% of code AI-generated)' } },
          y: { min: 0, title: { display: true, text: 'Efficiency ratio (participant ÷ reference runtime)' } }
        }
      }
    });
  }
  whenInView('chart-scatter-efficiency', init);
})();
</script>

The correlation is **r = –0.10** (n=19) — effectively zero. There is no meaningful linear relationship between self-reported AI usage and code runtime efficiency in this snapshot. That is worth stating plainly: whatever heavy AI users are or aren't good at, they are not writing systematically slower-executing code than low-AI users.

The red point is a clear outlier: a zero-AI participant whose solutions ran roughly twice as slow as the reference (ratio ≈ 2.1) across 11 challenges — the most attempts of any session. This person also achieved 96% accuracy, so they were writing correct but slow code. Removing this point shifts the correlation from –0.10 to –0.18 (still negligible). It is flagged here for transparency rather than removed, but it is worth watching whether this pattern persists if this participant returns for a second session.

---

## The Elephant in the Room: Confounding

The positive accuracy/completion correlations almost certainly don't mean what they appear to mean.

The most plausible explanation is **selection bias**: developers who adopted AI tools heavily are, on average, more experienced programmers. They got there first because they were already comfortable with the tooling and ecosystem. More experienced developers also perform better on coding challenges, regardless of AI usage.

In other words: **AI usage and coding ability may both be downstream of programming experience.** We could be measuring a correlation between two variables that share a common cause, with AI usage doing no causal work at all.

This is precisely why the study is *longitudinal*. The interesting question is not "do high AI users perform better right now?" — they do, probably because they were already better. The interesting question is: **does a participant's performance change as their AI usage changes?** Answering that requires multiple sessions per participant tracked over time.

Right now we have 19 participants with exactly one completed session and one person with two. That's not enough longitudinal data to say anything about the main hypothesis.

### Other Caveats Worth Noting

- **Self-report noise.** AI usage percentage is a rough self-estimate, not an instrumented measurement. People's sense of "how much AI I use" varies by task and recall period.
- **Session-level vs habit-level.** The post-session question asks about the *past month*, not the session itself. A participant who usually uses 90% AI is answering about their habits, not their behaviour in the challenge (which explicitly asks them not to use AI).
- **Challenge difficulty.** We don't control for which challenges each participant received. A session with harder challenges will naturally show lower accuracy, and challenge assignment is randomised not matched across participants.
- **Tiny N.** 20 sessions. r = 0.48 with n=20 has a 95% CI roughly from 0.05 to 0.74. The point estimate is almost meaningless at this sample size.

---

## What to Watch For

As sessions accumulate, the signal we're actually interested in comes from the `accuracy ~ vibe_coding_pct × months_since_baseline` interaction term in the multilevel model. In plain English:

- Does a participant who *increases* their AI usage over time show a performance change?
- Does a participant who *decreases* their AI usage show a different trajectory?
- Do these effects differ by challenge difficulty tier?

We're also watching the **speed variable** specifically. It showed a positive correlation with AI usage (slower = more AI) which is counter-intuitive if you assumed AI dependency manifests as giving up quickly. That's worth following across sessions.

One variable we can probably stop worrying about is **code efficiency**: the efficiency ratio showed no meaningful correlation (r = –0.10) and coverage is near-complete, so that null is fairly reliable at this sample size. Further sessions are unlikely to change the picture much unless the participant mix changes substantially.

The [study needs participants with multiple sessions](/session/start/) to answer any of these questions. If you've done one session, the most valuable thing you can do is come back in a month.

---

## Reproducibility

Every number in this post was computed from the production database using Django ORM queries run on 2026-05-24. The full analysis — queries, methodology, raw session data, and results — is logged in [`analysis/2026-05-24-ai-usage-correlation/`](https://github.com/andytwoods/agenticbrainrot/tree/master/analysis/2026-05-24-ai-usage-correlation). Anyone with access to the dataset can reproduce these results exactly.
