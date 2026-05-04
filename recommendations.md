Practice effects  –  the biggest methodological threat. Participants do coding challenges every month for a year+. That
alone will improve their skills, especially on Tier 1–2
problems. The non-vibe-coders will improve, the vibe-coders might improve less (or not at all)  –  but you're measuring a
difference in improvement rates, not absolute decline.
This is fine statistically (the interaction term captures it), but it needs to be clearly framed in any write-up. You
might also want a "no-practice" baseline  –  e.g. participants
who do sessions every 3 months instead of monthly, to estimate the practice effect size.

Selection bias. Who volunteers for a study called "does vibe coding make you worse?" Probably people already worried
about it, or people confident it doesn't. Either way, not a
random sample of developers. Worth acknowledging as a limitation and collecting Q23 (motivation) data to characterise
it.

Attrition bias. If participants who notice their skills declining drop out (demoralising), your surviving sample skews
toward people who are stable or improving. Consider
analysing dropout patterns  –  is dropout predicted by declining scores or high vibe-coding %?

Causality. This is observational. You can find that vibe-coding % predicts skill change, but not that it causes it. A
confounder like "people who are burning out code less
carefully AND adopt AI tools more" could explain both. Worth being upfront about this.

LeetCode problem licensing. The LeetCodeDataset on HuggingFace is a research dataset, but LeetCode's ToS prohibit
reproducing their problems commercially. You should check the
licence carefully – wthyou may need to stick to problems sourced from openly-licensed repos, or author Tier 1–2 problems
yourself (which you're already partly planning).

Pyodide load time. The WASM bundle is ~10–15MB. First load on a slow connection could take 10–30 seconds. Consider:
preloading while the participant reads instructions, showing a
progress bar, caching aggressively via service worker. If someone bounces because of load time, you've lost them.

Mobile. Coding on a phone is miserable. Should the app explicitly discourage mobile sessions, or block them? If someone
does attempt one, the timing data will be meaningless. At
minimum, detect mobile and warn; record device type as a covariate.

Cheating / AI use during challenges. You ask them not to use AI, but some will. Beyond the honour system, consider:
detecting paste events (large code blocks appearing
instantly), flagging suspiciously fast correct answers on hard problems, and recording keystroke cadence (typing vs.
pasting). None of these are proof, but they're useful
covariates for sensitivity analysis.

Multiple accounts. Nothing stops someone creating two accounts. If they're a genuine participant this is harmless but
pollutes the data. Consider email verification at minimum;
optionally flag accounts from the same IP.

Accessibility. No mention of screen readers, keyboard navigation, or colourblind-friendly charts. If this is a public
citizen-science project, accessibility matters both ethically and for sample diversity.

"Calendar month" enforcement across time zones. If the server is UTC but the participant is in UTC+12, "once per
calendar month" may feel unfair. Define it as "minimum 28 days
between sessions" rather than calendar month boundaries.

Ecological validity. LeetCode-style challenges test a specific slice of coding skill (algorithmic problem-solving,
syntax recall). They don't test debugging, reading others'
code, system design, or writing tests  –  skills that may also be affected by vibe coding. Worth acknowledging this as a
limitation. Could add other challenge types in later
phases.

Long-term maintenance. A 12+ month longitudinal study needs someone maintaining the server, fixing bugs, responding to
participants, and managing the community. Is this funded?
Do you have a team, or is it solo? This affects how ambitious the MVP should be.

Retention incentives beyond data. Rich personal dashboards are good, but after 6 months novelty wears off. Consider:
periodic email summaries ("Your skill trajectory this
quarter"), milestone badges (completed 5 sessions), and the social angle (anonymised leaderboards or cohort
comparisons). The citizen-science framing ("you're contributing to
real research") is powerful  –  lean into it with periodic blog posts about emerging findings.

Pre-registration. For a study making claims about vibe coding and skill, pre-registering the analysis plan (e.g. on OSF
or AsPredicted) before data collection would massively
boost credibility. Consider adding this to Phase 1 or early Phase 2.

Pilot testing. Before launch, run 10–15 people through the full flow (registration → consent → intake → session →
survey → results). You'll find UX issues, confusing questions,
and broken edge cases. Budget time for this.

Sample size for subgroup analyses. 200 participants is enough for the main effect, but if you want to slice by industry,
role, experience level, or LeetCode familiarity, you need
larger cells. Consider whether recruitment should be targeted to ensure enough variance in key predictors.
