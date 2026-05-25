---
title: Early Signals: AI Usage and Coding Performance
date: 2026-05-24
author: Andy T Woods
summary: "High AI users outperform low AI users in our first 20 sessions. That sounds like the exact opposite to <a href=\"https://github.com/andytwoods/agenticbrainrot/blob/master/preregistration/aspredicted.md\">our predictions</a>! But this exemplifies why longitudinal design matters. An across-person snapshot can&#39;t separate skill from selection bias; only within-person tracking over time can."
analysis_ref: 2026-05-24-ai-usage-correlation
---

## 20 sessions in. An unexpected twist, and why you shouldn't read too much into it just yet.

An aim of this project is to test whether heavy use of AI coding tools impact our ability to code. We don't have enough data to answer that just yet. But we do have enough early data to run a sanity check – and the early data at first glance is quite surprising! With some deliberation, though, the unexpected findings nicely demonstrate the importance of a more robust design, that factors in coding ability change over time – which we can test when enough people have signed up ([please do!](/allauth/signup/)) :)

All numbers in this post are reproducible from the [analysis log](https://github.com/andytwoods/can-I-still-code/tree/master/analysis/2026-05-24-ai-usage-correlation).

<div class="notification is-info is-light">
<strong>Key terms used in this post</strong><br>
<strong>Challenge</strong> – a single Python coding problem. Participants write code in the browser; automated tests check whether it works.<br>
<strong>Session</strong> – one sitting in which a participant completes a batch of up to 12 challenges. Sessions are separated by at least 28 days.<br>
<strong>Participant</strong> – one person enrolled in the study. A participant may have one or more sessions over time.<br>
<strong>AI usage %</strong> – self-reported answer to: <em>"In the past month, roughly what percentage of the code you wrote was AI-generated?"</em> (0–100).
</div>

---

## Why longitudinal design matters – and why this data shows it

The surprising finding: higher AI usage correlates *positively* with accuracy (r = +0.48). In this very early cross-sectional snapshot, people reporting higher AI usage also tended to score higher on the challenges.

The issue though is that we're only seeing most people once and we can't tell yet whether high-AI users are doing well *because* of their habits, *despite* them, or simply because they were already stronger coders before any of this started. Early adopters of AI tools potentially also could be experienced developers – and experienced developers will do better at coding challenges. 

To untangle this we need to follow the same people over time – the plan is that participants come back several times during the year to do further tests so we can observe if heavy AI usage is impacting individuals over time. 

---

## What We Have

As of May 2026 we have **20 completed sessions** from **19 participants**. Each session involves solving Python challenges without AI assistance, followed by a short post-session survey. That survey includes the key question:

> *In the past month, roughly what percentage of the code you wrote was AI-generated?*


### Who took part

All participants are adults aged 25–54. Across the 20 sessions: nine from participants in the 25–34 age bracket, seven in 35–44, four in 45–54. (One participant has completed two sessions, so session counts exceed the 19 unique individuals by one.) This is an experienced group – average programming experience is around **14 years** (range 4–30), with roughly **9 years using Python** specifically. Self-rated proficiency skews intermediate to advanced: 9 sessions from intermediate-rated participants, 8 advanced, 2 somewhat beginner, 1 expert. Exactly half have a CS or related degree; half don't. Most are based in the UK (14 of 19 unique participants), with the remainder spread across Germany, Switzerland, and Sweden.

On average participants attempted **4.8 challenges per session** (range 1–12 – the maximum per session is 12).

We don't currently collect gender data, which is a gap we're aware of.

### The Four Outcome Variables

For each session we collect/compute:

| Variable | Definition |
|---|---|
| **Accuracy** | Average `tests_passed / tests_total` across challenges, expressed as a % |
| **Completion rate** | % of attempted challenges where *all* test cases passed |
| **Speed** | Average wall-clock time in seconds per challenge |
| **Efficiency ratio** | Participant solution runtime ÷ reference solution runtime. 1.0 = matched canonical; >1 = slower-running code |

The first three map directly to the primary outcomes in the [study design](/about): accuracy, speed, and completion as a proxy for overall success. Efficiency ratio is a secondary measure of code quality – whether participants write solutions that run snappily!

---

## What We Found

<div class="notification is-warning is-light">
<strong>Important caveat before the charts:</strong> this is a cross-sectional snapshot of 20 sessions, mostly single observations per person. The correlations tell us about the relationship between AI usage and <em>current</em> performance – they say nothing about how performance <em>changes over time</em> as AI usage changes. That question requires longitudinal data, which we don't have yet.
</div>

### Correlations with AI Usage

Simple Pearson correlations between reported AI usage percentage and each outcome:

| Outcome | r | n | Rough interpretation |
|---|---|---|---|
| Accuracy | **+0.48** | 20 | Moderate positive |
| Completion rate | **+0.32** | 20 | Weak-to-moderate positive |
| Time per challenge | **+0.31** | 20 | Weak positive |
| Efficiency ratio | **–0.10** | 19 | Negligible |

*p-values are not emphasised. At this sample size and with exploratory analyses, they would invite over-interpretation – r=0.48 scrapes past p<0.05, but that threshold carries almost no weight with n=20. The r values and 95% CIs are what matter.*

*Two further limitations on these correlations: (a) accuracy and completion rate are bounded at 0–100% and already show ceiling effects for high-AI users, so Pearson r is a brittle summary even as a descriptive measure; (b) each session contributes equally to the correlation regardless of how many challenges were attempted – a 1-challenge session carries the same weight as a 12-challenge session.*

Three of the four correlations are positive – higher AI use goes with better accuracy, more completions, and (oddly) more time taken. We'll come back to why "AI users are better coders" is almost certainly the wrong read.

Worth flagging upfront: Pearson r is also the wrong tool for the actual research question. It describes a between-person relationship – do high-AI users score higher than low-AI users? – but what we care about is within-person change: does *your* performance shift as *your* AI usage shifts? Those are completely different questions, and the between-person version is hopelessly confounded by experience. The [planned analysis](https://github.com/andytwoods/agenticbrainrot/blob/master/preregistration/aspredicted.md) uses mixed-effects models with person-mean centring, so each participant acts as their own control – a much more powerful approach, but one that requires multiple sessions per person.

### Performance by AI Usage Group

Splitting sessions into three bands by reported AI usage:

<div class="chart-wrap">
  <canvas id="chart-groups" style="max-height:380px"></canvas>
</div>

<script>
(function () {
  var isMobile = window.innerWidth < 768;
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
        maintainAspectRatio: false,
        plugins: {
          legend: { position: isMobile ? 'bottom' : 'top' },
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

This grouping is purely illustrative – with only four sessions in the low-AI band (one of which scored 0%), the apparent accuracy jump from 62% to 99.5% should not be read as a stable group difference. It is a descriptive split on a very small sample.

### AI Usage vs Accuracy (per session)

Each bubble below is one session. Bubble size is proportional to the number of challenges attempted.

<div class="chart-wrap">
  <canvas id="chart-scatter-accuracy" style="width:100%;height:100%"></canvas>
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
  var isMobile = window.innerWidth < 768;
  var rScale = isMobile ? 0.6 : 1;
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
    var scaled = bubbles.map(function(p) { return {x: p.x, y: p.y, r: p.r * rScale, n: p.n}; });
    var bgColors = scaled.map(function(_, i) { return i === OUTLIER_IDX ? outlierBg : defaultBg; });
    var borderColors = scaled.map(function(_, i) { return i === OUTLIER_IDX ? outlierBorder : defaultBorder; });
    new Chart(ctx, {
      type: 'bubble',
      data: {
        datasets: [
          {
            label: 'Session',
            data: scaled,
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
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          title: { display: true, text: 'AI Usage % vs Challenge Accuracy (bubble size = challenges attempted)' },
          tooltip: {
            filter: function(item) { return item.datasetIndex === 0; },
            callbacks: {
              label: function(c) {
                var base = 'AI: ' + c.raw.x + '%  |  Accuracy: ' + c.raw.y + '%  |  n=' + c.raw.n;
                return c.dataIndex === OUTLIER_IDX ? base + '  ⚑ flagged' : base;
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

At AI% = 0 there's a lot of spread – some zero-AI participants did really well, others didn't. The red point is one person who passed zero challenges in their only attempt, the worst result in the dataset. It drags the low-AI group average down and nudges the correlation up. We've flagged it but not removed it: our pre-registered rules only exclude sessions on timing grounds, and this one is fine. Up at high AI usage the sessions clump near 100% with almost no spread. Whether that's genuine ability or something else is what the longitudinal data will eventually tell us.

### The Speed Paradox

Here's an interesting finding. If AI dependency were degrading coding ability, you might expect high-AI users to take longer, and indeed they do! But they're *also* more accurate. So what's going on?

*Note: this uses raw wall-clock time, not the pre-registered active-time measure (log of active completion time). Wall-clock time can include reading, pausing, and tab switching, so treat it as a noisy behavioural indicator rather than a precise measure.*

<div class="chart-wrap">
  <canvas id="chart-scatter-speed" style="width:100%;height:100%"></canvas>
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
  var isMobile = window.innerWidth < 768;
  var rScale = isMobile ? 0.6 : 1;
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
    var scaled = bubbles.map(function(p) { return {x: p.x, y: p.y, r: p.r * rScale, n: p.n}; });
    new Chart(ctx, {
      type: 'bubble',
      data: {
        datasets: [
          {
            label: 'Session',
            data: scaled,
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
        maintainAspectRatio: false,
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

High AI users (>75%) average **183 seconds** per challenge versus 112 seconds for low AI users – they're slower *and* more accurate. Three possible explanations, each worth tracking as data accumulates:

1. **Challenge difficulty confound.** Challenges are randomly assigned and vary in difficulty; sessions are not matched. If high-AI users (who are generally more experienced) attempt more challenges per session – including harder, more time-consuming ones that less experienced participants might skip or abandon early – their average time goes up purely because of what they chose to attempt. This is probably the most mundane explanation.
2. **Heavy AI users tackle harder challenges more persistently** – instead of giving up quickly, they grind through. We can check this against challenge difficulty tier data once we have more sessions.
3. **Pacing habits transferred from AI-assisted work** – people used to iterating with AI feedback may naturally take more time verifying their solutions manually, even though they're ultimately right.

### Code Efficiency: A Null Result

We also track how fast participants' code actually runs – the **efficiency ratio** is execution time relative to a reference solution (1.0 = matched; above 1 = slower). Coverage is good: 94 of 96 attempts have a value.

<div class="notification is-success is-light">
<strong>How it works:</strong> when you submit a solution, both your code <em>and</em> the reference answer are executed in the browser via <a href="https://pyodide.org/">Pyodide</a>. We take a median over 15 timing samples for each, divide participant time by reference time, and send only that ratio to the server. No submitted code is ever executed on our infrastructure. Reference solutions come from the original published benchmarks (MBPP, HumanEval) where available. <a href="https://github.com/andytwoods/can-I-still-code/tree/master/analysis/2026-05-24-ai-usage-correlation#efficiency-ratio-methodology">Full methodology in the analysis log &nearr;</a>
</div>

<div class="chart-wrap">
  <canvas id="chart-scatter-efficiency" style="width:100%;height:100%"></canvas>
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
  var isMobile = window.innerWidth < 768;
  var rScale = isMobile ? 0.6 : 1;
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
    var scaled = bubbles.map(function(p) { return {x: p.x, y: p.y, r: p.r * rScale, n: p.n}; });
    var bgColors = scaled.map(function(_, i) { return i === OUTLIER_IDX ? outlierBg : defaultBg; });
    var borderColors = scaled.map(function(_, i) { return i === OUTLIER_IDX ? outlierBorder : defaultBorder; });
    new Chart(ctx, {
      type: 'bubble',
      data: {
        datasets: [
          {
            label: 'Session',
            data: scaled,
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
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          title: { display: true, text: 'AI Usage % vs Code Efficiency Ratio (bubble size = challenges attempted)' },
          tooltip: {
            filter: function(item) { return item.datasetIndex === 0; },
            callbacks: {
              label: function(c) {
                var base = 'AI: ' + c.raw.x + '%  |  efficiency: ' + c.raw.y + '×  |  n=' + c.raw.n;
                return c.dataIndex === OUTLIER_IDX ? base + '  ⚑ flagged' : base;
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

The correlation is **r = –0.10** – basically flat. In this tiny snapshot, there's no visible evidence that high-AI users write slower-running code than low-AI users. That's actually a useful early signal.

The red point is one person who solved 11 challenges correctly but ran about twice as slow as the reference. Remove them and the correlation shifts to –0.18 – still nothing. Flagged for transparency, not excluded (same timing-based rule applies). One to revisit if they come back for a second session.

---

## A Few Caveats

As covered above, the positive correlations almost certainly reflect selection bias rather than anything causal – experienced developers adopted AI tools early *and* score higher on challenges. Both trace back to experience. The longitudinal design is how we get past this.

A few other things worth bearing in mind:

- **Self-report noise.** AI usage % is a rough estimate, not a measured one. People's sense of how much AI they use varies a lot by task and by how far back they're trying to recall.
- **Habits vs. the session.** The survey asks about the *past month*, not the session itself. Someone who normally uses AI 90% of the time is describing their habits – they weren't using AI during the challenge (we ask them not to).
- **Challenge difficulty varies.** Challenges are assigned randomly, so a session with harder problems will naturally score lower. We're not matching difficulty across participants at this stage.
- **Tiny N.** 20 sessions. r = 0.48 at n=20 has a 95% CI of roughly 0.05 to 0.74. The number itself should be taken loosely.

---

## What to Watch For

The signal we actually care about won't appear until people have done multiple sessions. We're looking for whether someone's accuracy *shifts* when their AI use goes up or down – that within-person change is the whole point. One session per person tells us nothing about that.

Speed is the one thing worth keeping an eye on for now. High-AI users are slower but more accurate, which doesn't fit the obvious story of AI dependency making people give up sooner. That's worth tracking.

**If you want to help answer the question, take part.** The more participants who complete multiple sessions, the faster the longitudinal signal emerges. Each session takes around 30–60 minutes and can be done entirely in your browser – no setup needed.

<div class="notification is-primary is-light">
  <strong>Take part in the study</strong><br>
  <a href="/allauth/signup/" class="button is-primary mt-2 mr-2">Create an account &rarr;</a>
  <a href="/waitlist/" class="button is-light mt-2">Join the waitlist</a>
</div>

---

## Pre-registration and Deviations

This study is pre-registered on AsPredicted – the full protocol is [on GitHub](https://github.com/andytwoods/agenticbrainrot/blob/master/preregistration/aspredicted.md). Pre-registration means we committed our hypotheses, analysis plan, and exclusion rules to a timestamped public record *before* collecting data, so there is no ambiguity about what was predicted in advance versus what was noticed after the fact. **This blog post is not the pre-registered analysis.** It is an exploratory cross-sectional snapshot run at 20 sessions to establish a baseline and demonstrate the study's data pipeline. The pre-registered primary analysis – a within-person longitudinal mixed model – will run when at least 100 participants have completed three or more sessions.

Here's exactly how this post's analysis differs from the pre-registered plan:

| Aspect | Pre-registered | This post |
|---|---|---|
| Study design | Longitudinal within-person | Cross-sectional, one timepoint per person |
| Unit of analysis | Challenge attempt | Session average |
| Primary predictor | Previous-session AI%, person-mean centred (lagged) | Current-session AI%, uncentred |
| Accuracy measure | Binary pass/fail per challenge | Mean tests_passed ÷ tests_total % |
| Speed measure | log(active completion time) | Raw wall-clock seconds |
| Statistical method | Mixed models – `lme4`, participant × session × challenge random effects | Pearson r |
| Outlier/exclusion rules | Completion time >3 h removed; <10 s excluded in sensitivity analyses only; no further removal | Not applied – session-level averages are not subject to per-attempt time rules |
| Minimum sample | 100 participants × ≥3 sessions | 20 sessions, 19 participants |

Two sessions are flagged in red (0% accuracy and efficiency ratio ≈ 2.1). Neither is excluded – the pre-registration only removes sessions on timing grounds, and both are fine on that score. The red dots are just there so you know we've seen them.

**One potential future deviation under consideration:** we may want to exclude participants who pass zero challenges across all sessions – essentially a failed engagement screen, not a true study observation. The [pre-registered exclusion rules](https://github.com/andytwoods/agenticbrainrot/blob/master/preregistration/aspredicted.md) don't cover this case. If we decide to apply it, it will be logged here as a formal deviation before any primary analysis runs.

---

## Reproducibility

Every number here was pulled from the production database on 2026-05-24. Methodology and anonymised session data are in [`analysis/2026-05-24-ai-usage-correlation/`](https://github.com/andytwoods/can-I-still-code/tree/master/analysis/2026-05-24-ai-usage-correlation) on GitHub.
