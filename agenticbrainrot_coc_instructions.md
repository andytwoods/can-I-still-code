# Instructions: Add a Code of Conduct to AgenticBrainrot

## Context

AgenticBrainrot (agenticbrainrot.applikuapp.com) is a citizen-science longitudinal study measuring whether AI-assisted ("vibe") coding leads to coding skill degradation. It is a Django web app. These instructions are for adding a Code of Conduct with a reporting mechanism, which is a prerequisite for PSF Community Partner application.

---

## What to do

### 1. Create `CODE_OF_CONDUCT.md` in the repo root

Base it on the **Contributor Covenant v2.1** (https://www.contributor-covenant.org/version/2/1/code_of_conduct/) — this is what the PSF recognises and recommends.

Adapt it to this project's context:
- Scope: participation in the study, the GitHub repo, and any community spaces (e.g. issues, discussions)
- Replace generic "project maintainers" with "AgenticBrainrot maintainers"
- Tailor the pledge section to reflect an open research community (participants, contributors, researchers)

The reporting section **must** include:
- A named contact email address (use Andrew's institutional email or a dedicated address — confirm with Andrew before committing)
- A brief description of what happens after a report is received (acknowledgement within X days, investigation, outcome communicated)
- A statement that all reports will be handled confidentially
- An alternative contact if the reporter has a conflict of interest with the primary contact

### 2. Add a `/code-of-conduct/` page to the Django app

- Create a minimal template: `templates/code_of_conduct.html`
- Render the CoC content (can be static HTML or pulled from the markdown file via a template tag)
- Add a URL route: `path('code-of-conduct/', views.code_of_conduct, name='code_of_conduct')`
- Add a simple view that renders the template
- Link to it from the site footer on every page

### 3. Link from README.md

Add a "Code of Conduct" badge or link near the top of `README.md`:

```markdown
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)
```

---

## Key requirements (for PSF compatibility)

- Must use a recognised CoC (Contributor Covenant is the standard choice)
- Must include a **specific reporting mechanism** — a generic "contact the maintainers" is not sufficient; a real email address is required
- Must be publicly accessible at a URL (the `/code-of-conduct/` page satisfies this)
- Must be linked from the project's main presence (README + website footer)

---

## What NOT to do

- Do not write a bespoke CoC from scratch — use Contributor Covenant as the base
- Do not leave the reporting email as a placeholder — confirm the real address before committing
- Do not bury the CoC only in the repo; it must be on the live website

---

## Commit message

```
add: Code of Conduct (Contributor Covenant 2.1) with reporting mechanism
```
