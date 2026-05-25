---
title: "Early results: AI Users Code Better by Hand – But It's Very Likely Not Why You Think"
date: 2026-05-24
author: Andy T Woods
summary: "High AI users outperform low AI users in our first 20 sessions. That sounds like the exact opposite of <a href=\"https://github.com/andytwoods/agenticbrainrot/blob/master/preregistration/aspredicted.md\">our predictions</a>! But this exemplifies why longitudinal design matters. An across-person snapshot can't separate skill from selection bias; only within-person tracking over time can."
analysis_ref: 2026-05-24-ai-usage-correlation
---

One aim of this project is to test whether heavy use of AI coding tools affects our ability to code. We don't have enough data to answer that just yet. But we can eyeball our data, and the first-glance results are surprising: participants who reported higher AI usage performed better on the coding challenges (r = +0.48 with accuracy) – but were also slower (r = +0.27 with active time per challenge).

That is almost certainly not evidence that AI use improves unaided coding skill! With such a tiny sample size (19 people) we can't make any conclusions. But it is interesting to ponder what it would mean if we continued observing this pattern of results. One explanation could be is that we have confounding factors at play, for example, that early AI adopters in this sample may be stronger coders. We can test this by checking whether experience drives AI adoption directly: the correlation between programming years and AI usage is r = −0.21 (n=32), and between Python-specific years and AI usage r = +0.25 (n=32). Both are weak and point in opposite directions, so experience doesn't cleanly explain the pattern. Another idea is that our average number of years coding is very high (approx 14). It may only be by recruiting partiicpants with a broader range of coding abilities are we able to properly test our hypotheses.  

We dont know whats going on yet. Note here we have a tiny sample (19 people, 20 sessions) and need far more participants to reliably explore this. Also, we can only adequately test this by testing people's coding skills over time, which provides a much more robust way of checking our hypotheses.

We'd very much appreciate it if you could spread the word and also [sign up!](/allauth/signup/) :)

All numbers in this post are reproducible from the [analysis log](https://github.com/andytwoods/can-I-still-code/tree/master/analysis/2026-05-24-ai-usage-correlation).

---
**Key terms used in this post**

| Term | Definition |
|---|---|
| **Challenge** | A single Python coding problem. Participants write code in the browser; automated tests check whether it works. |
| **Session** | One sitting in which a participant completes a batch of up to 12 challenges. Sessions are separated by at least 28 days. |
| **Participant** | One person enrolled in the study. A participant may have one or more sessions over time. |
| **AI usage %** | Self-reported answer to: *"In the past month, roughly what percentage of the code you wrote was AI-generated?"* (0–100). |

---
## What we found

<div class="notification is-warning is-light">
<strong>Important caveat before the charts:</strong> this is a cross-sectional snapshot of 20 sessions, mostly single observations per person. The correlations tell us about the relationship between AI usage and <em>current</em> performance – they say nothing about how performance <em>changes over time</em> as AI usage changes. That question requires longitudinal data, which we don't have yet.
</div>

### Correlations with AI usage

Pearson correlations between reported AI usage percentage and each outcome:

| Outcome | r | n | Rough interpretation |
|---|---|---|---|
| Accuracy | **+0.48** | 20 | Moderate positive |
| Completion rate | **+0.32** | 20 | Weak-to-moderate positive |
| Active time per challenge | **+0.27** | 20 | Weak positive |
| Efficiency ratio | **–0.10** | 19 | Negligible |

*p-values are not added, because at this sample size, they would invite over-interpretation. 

Three of the four correlations are positive – higher AI use goes with better accuracy, more completions, and, oddly, more time taken. 

It is worth flagging that Pearson r is the wrong tool for the actual research question. It describes a between-person relationship – do high-AI users score higher than low-AI users? – but what we care about is within-person change: does *your* performance shift as *your* AI usage shifts? Those are completely different questions, and the between-person version is hopelessly confounded by experience.

The [planned analysis](https://github.com/andytwoods/agenticbrainrot/blob/master/preregistration/aspredicted.md) uses mixed-effects models with person-mean centring, so each participant acts as their own control. That is a much more powerful approach, but it requires multiple sessions per person.

### AI usage vs accuracy, per session

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

The red point is one person who passed zero challenges in their only attempt, the worst result in the dataset. It drags the low-AI group average down and nudges the correlation up. We've flagged it but not removed it: our pre-registered rules only exclude sessions on timing grounds, and this one is fine.

### Performance by AI usage group

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

This grouping is purely illustrative. With only four sessions in the low-AI band, one of which scored 0%, the apparent accuracy jump from 62% to 99.5% should not be read as a stable group difference. It is simply a descriptive split on a very small sample.

### The speed paradox

Here's an interesting finding. If AI dependency were reducing coding ability, you might expect high-AI users to take longer. In this early snapshot, they do. But they are *also* more accurate. So what's going on?

*Note: this uses active time – seconds where keystrokes occurred – not the pre-registered log-transformed active time that will be used in the primary mixed model. The values here are untransformed and suitable for this descriptive snapshot only.*

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
      {x: 0,  y: 72.0,  r: 7,  n: 6},
      {x: 0,  y: 88.4,  r: 7,  n: 5},
      {x: 0,  y: 198.5, r: 10, n: 11},
      {x: 30, y: 123.8, r: 7,  n: 5},
      {x: 30, y: 114.0, r: 4,  n: 1},
      {x: 33, y: 103.0, r: 6,  n: 4},
      {x: 50, y: 254.5, r: 10, n: 11},
      {x: 50, y: 136.5, r: 5,  n: 2},
      {x: 50, y: 193.3, r: 5,  n: 3},
      {x: 50, y: 60.7,  r: 8,  n: 7},
      {x: 50, y: 37.0,  r: 6,  n: 4},
      {x: 75, y: 128.0, r: 4,  n: 1},
      {x: 75, y: 116.3, r: 7,  n: 6},
      {x: 85, y: 168.0, r: 4,  n: 1},
      {x: 90, y: 201.3, r: 10, n: 10},
      {x: 90, y: 66.0,  r: 4,  n: 1},
      {x: 90, y: 33.8,  r: 6,  n: 4},
      {x: 95, y: 393.0, r: 4,  n: 1},
      {x: 95, y: 149.2, r: 10, n: 12}
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
          title: { display: true, text: 'AI Usage % vs Active Time per Challenge (bubble size = challenges attempted)' },
          tooltip: {
            filter: function(item) { return item.datasetIndex === 0; },
            callbacks: {
              label: function(c) {
                return 'AI: ' + c.raw.x + '%  |  active: ' + c.raw.y + 's  |  n=' + c.raw.n;
              }
            }
          }
        },
        scales: {
          x: { min: -5, max: 105, title: { display: true, text: 'Self-reported AI usage (% of code AI-generated)' } },
          y: { min: 0, title: { display: true, text: 'Active seconds per challenge' } }
        }
      }
    });
  }
  whenInView('chart-scatter-speed', init);
})();
</script>

High AI users (>75%) average **169 seconds** of active time per challenge versus 110 seconds for low AI users. They are slower *and* more accurate. Three possible explanations are worth tracking as data accumulates:

1. **Challenge difficulty confound.** Challenges are randomly assigned and vary in difficulty; sessions are not matched. If high-AI users, who are generally more experienced in this early sample, attempt more challenges per session – including harder, more time-consuming ones that less experienced participants might skip or abandon early – their average time goes up because of what they chose to attempt. This is probably the most mundane explanation.
2. **Heavy AI users tackle harder challenges more persistently.** Instead of giving up quickly, they may grind through. We can check this against challenge difficulty tier data once we have more sessions.
3. **Pacing habits may transfer from AI-assisted work.** People used to iterating with AI feedback may naturally take more time verifying their solutions manually, even though they ultimately get them right.

### Code efficiency: a null result

We also track how fast participants' code actually runs. The **efficiency ratio** is execution time relative to a reference solution: 1.0 means matched; above 1 means slower. Coverage is good: 94 of 96 attempts have a value.

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

The correlation is **r = –0.10**. There is no visible evidence that high-AI users write slower-running code than low-AI users. 

The red point is one person who solved 11 challenges correctly but ran about twice as slow as the reference. They reported 0% AI usage. Remove them and the correlation shifts to **+0.33** – because this low-AI, high-efficiency-ratio point was pulling the correlation negative. So the efficiency picture is sensitive to a single outlier, and the sign is not stable. The point is flagged for transparency, not excluded, because the pre-registered rules only remove sessions on timing grounds. This is one to revisit if they return for a second session.

---

## In more detail

As of May 2026 we have **20 completed sessions** from **19 participants**. Each session involves solving Python challenges without AI assistance, followed by a short post-session survey. That survey includes the key question:

> *In the past month, roughly what percentage of the code you wrote was AI-generated?*

### Who took part

All participants are adults aged 25–54. Across the 20 sessions, nine are from participants in the 25–34 age bracket, seven in 35–44, and four in 45–54. One participant has completed two sessions, so the session count is 20.

This is an experienced group. Average programming experience is around **14 years** (range 4–30), with roughly **9 years using Python** specifically. Self-rated proficiency skews intermediate to advanced: 9 sessions from intermediate-rated participants, 8 advanced, 2 somewhat beginner, and 1 expert. Exactly half have a CS or related degree; half don't. Most are based in the UK (14 of 19 unique participants), with the remainder spread across Germany, Switzerland, and Sweden.

On average, participants attempted **4.8 challenges per session** (range 1–12; the maximum per session is 12).

### The four outcome variables

For each session we collect or compute:

| Variable | Definition |
|---|---|
| **Accuracy** | Average `tests_passed / tests_total` across challenges, expressed as a % |
| **Completion rate** | % of attempted challenges where *all* test cases passed |
| **Speed** | Average wall-clock time in seconds per challenge |
| **Efficiency ratio** | Participant solution runtime ÷ reference solution runtime. 1.0 = matched canonical; >1 = slower-running code |

The first three map directly to the primary outcomes in the [study design](/about): accuracy, speed, and completion as a proxy for overall success. Efficiency ratio is a secondary measure of code quality – whether participants write solutions that run snappily.

---

## A few caveats

As covered above, the positive correlations almost certainly reflect selection bias rather than anything causal. The experience confound is less clean than it first appears — programming years and AI usage correlate at r = −0.21, Python years at r = +0.25 (both n=32, both weak). So experience alone doesn't account for the pattern, but we can't rule out other selection effects. The longitudinal design is how we get past this.

A few other things are worth bearing in mind:

- **Self-report noise.** AI usage % is a rough estimate, not a measured one. People's sense of how much AI they use varies a lot by task and by how far back they're trying to recall.
- **Habits vs. the session.** The survey asks about the *past month*, not the session itself. Someone who normally uses AI 90% of the time is describing their habits – they weren't using AI during the challenge, because we ask them not to.
- **Challenge difficulty varies.** Challenges are assigned randomly, so a session with harder problems will naturally score lower. We're not matching difficulty across participants at this stage.
- **Tiny N.** 20 sessions. r = 0.48 at n = 20 has a 95% CI of roughly [0.04, 0.76]. The number itself should be taken loosely.

---

## What to watch for

The signal we actually care about won't appear until people have completed multiple sessions. We're looking for whether someone's accuracy *shifts* when their AI use goes up or down. That within-person change is the whole point. One session per person tells us very little about that.

Speed is the one thing worth keeping an eye on for now. High-AI users are slower but more accurate, which doesn't fit the obvious story of AI dependency making people give up sooner. That's worth tracking.

**If you want to help answer the question, take part.** The more participants who complete multiple sessions, the faster the longitudinal signal emerges. Each session takes around 30–60 minutes and can be done entirely in your browser – no setup needed.

<div class="notification is-primary is-light">
  <strong>Take part in the study</strong><br>
  <a href="/allauth/signup/" class="button is-primary mt-2 mr-2">Create an account &rarr;</a>
  <a href="/waitlist/" class="button is-light mt-2">Join the waitlist</a>
</div>

---

## Pre-registration and deviations

This study is pre-registered on AsPredicted. The full protocol is [on GitHub](https://github.com/andytwoods/agenticbrainrot/blob/master/preregistration/aspredicted.md). Pre-registration means we committed our hypotheses, analysis plan, and exclusion rules to a timestamped public record *before* collecting data, so there is no ambiguity about what was predicted in advance versus what was noticed after the fact.

**[This blog post is not the pre-registered analysis.](https://github.com/andytwoods/agenticbrainrot/blob/master/preregistration/aspredicted.md)** It is an exploratory cross-sectional snapshot run at 20 sessions to establish a baseline and demonstrate the study's data pipeline. The pre-registered primary analysis – a within-person longitudinal mixed model – will run when at least 100 participants have completed three or more sessions.

Two sessions are flagged in red: one with 0% accuracy and one with an efficiency ratio of approximately 2.1. Neither is excluded – the pre-registration only removes sessions on timing grounds, and both are fine on that score. The red dots are included so you know we've seen them.

**One potential future deviation under consideration:** we may want to exclude participants who pass zero challenges across all sessions – essentially a failed engagement screen, not a true study observation. The [pre-registered exclusion rules](https://github.com/andytwoods/agenticbrainrot/blob/master/preregistration/aspredicted.md) don't cover this case. If we decide to apply it, it will be logged here as a formal deviation before any primary analysis runs.

---

## Reproducibility

Every number here was pulled from the production database on 2026-05-24. Methodology and anonymised session data are in [`analysis/2026-05-24-ai-usage-correlation/`](https://github.com/andytwoods/can-I-still-code/tree/master/analysis/2026-05-24-ai-usage-correlation) on GitHub.
