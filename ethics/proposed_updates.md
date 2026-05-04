# Proposed Protocol Updates

Changes being considered for a formal ethics amendment. Add items here as they arise, then batch into a single amendment submission.

---

## 1. Per-challenge feedback questions (level-0 / screening arm)

**What:** Add short questions attached to individual challenges, presented immediately after the participant submits their answer. Two types proposed:
- Subjective confidence rating, e.g. "How confident did you feel on that problem?" (Likert scale or similar)
- Multiple-choice comprehension/reflection, e.g. "Which answer is closest to what you wrote?" or "What approach did you take?"

**Why it may need an amendment:** The approved post-session survey covers AI coding habits only. Per-challenge questions are a new data collection instrument not described in the approved protocol.

**Data collected:** Per-challenge subjective ratings and/or multiple-choice responses, linked to participant ID and challenge ID.

**Participant burden:** Minimal -- a few seconds per challenge. Participants can still skip or withdraw at any point.

**Status:** Under consideration

---

## 2. Per-challenge qualitative data collection via AI-mediated interview

**What:** After submitting a challenge answer, participants are invited to give a qualitative account of their experience of that specific challenge (e.g. what they found difficult, their reasoning process, what they were uncertain about). The proposed method is a short conversational AI interview -- a natural language exchange driven by an AI system -- rather than a static free-text box.

**Why it may need an amendment:** The approved qualitative strand covers only an end-of-study exit survey and optional semi-structured video interviews with a researcher. Per-challenge qualitative responses are a new instrument. An AI-mediated interview is a materially different method from both static free text and researcher-led interviews, and will require specific scrutiny on:

- **Disclosure:** Participants must be clearly informed they are interacting with an AI system, not a human researcher.
- **AI system and data routing:** The specific AI system used (model, provider, API) must be identified. Any data sent to a third-party AI provider constitutes a data transfer that must be covered by the GDPR data management plan and relevant data processing agreements.
- **Transcript storage:** Conversational transcripti thin s are richer and potentially more identifying than Likert responses. Retention, pseudonymisation, and public release policies need explicit coverage.
- **Scope control:** The AI interview must be constrained to challenge-relevant topics to avoid eliciting sensitive disclosures outside the study's scope.
- **Participant burden and opt-out:** Participation in the AI interview should be optional, with a simple skip mechanism.

**Data collected:** Per-challenge conversational transcripts, linked to participant ID and challenge ID.

**EU provider options:** To keep all data processing within the EU (consistent with current Hetzner hosting) and simplify the GDPR case, candidate providers are:
- **Mistral AI** (Paris) -- conversational API, EU-incorporated, GDPR DPA available. Likely the simplest path for an amendment submission.
- **Aleph Alpha** (Heidelberg) -- German company, strong EU data sovereignty guarantees, enterprise/research-focused. Most defensible but more expensive.
- **Hugging Face Inference Endpoints** (French company, EU-region deployment) -- open-source models on EU infrastructure, more setup required.
- **Self-hosted on existing Hetzner VPS** -- run a model locally (e.g. Mistral 7B via Ollama); no third-party data transfer at all, making the GDPR position trivial. Trade-off is interview quality and server load.

**Input method:** Voice-to-text via Whisper WASM (Transformers.js), running entirely in the browser. Audio is never transmitted or stored -- only the resulting text transcript reaches the server. Participants who cannot or prefer not to use voice can type instead.

Participants select their preferred Whisper model before first use, trading off download size against accuracy:
Early study results
| Model           | Download | Accuracy                        |
|-----------------|----------|---------------------------------|
| tiny (quantized)| ~35MB    | Good for conversational English |
| base            | ~142MB   | Noticeably better               |
| small           | ~466MB   | Near-server quality             |

Model weights are downloaded directly from Hugging Face's CDN to the participant's browser and cached locally -- they are never routed through the study server. Model choice is recorded as a metadata field on transcripts so any accuracy differences between model tiers can be accounted for in analysis.

**Status:** Under consideration -- EU provider for the AI interview component to be confirmed before amendment is drafted.

---

## 3. Extended answer recording and automated code metrics

Two related but distinct additions:

### 3a. Automated metrics on submitted code
**What:** Compute automated metrics on the code participants submit, beyond the currently approved pass rate and completion time. Candidates include cyclomatic complexity, lines of code, use of built-ins vs manual loops, and efficiency proxies.

**Why it may need an amendment:** The approved protocol records performance outcomes (pass/fail, time). Storing and analysing the code itself as a research artefact -- and deriving structural metrics from it -- is not explicitly described. Coding style can also be more personally identifying than a pass rate, so the data management plan may need updating.

### 3b. Recording intermediate attempts (per check-button click)
**What:** Record the participant's code each time they click the "check" / "run tests" button, not only on final submission. This creates a sequence of attempts capturing how their solution evolved during the challenge.

**Why it may need an amendment:** This is materially richer data than a single final answer. Key considerations:
- **Informed consent:** Participants should be explicitly told that each check attempt is recorded, not just their final answer. The current consent form likely does not cover this.
- **Data volume and storage:** A full attempt sequence per challenge per session is significantly more data. The data management plan should reflect this.
- **Identifiability:** An attempt sequence (incremental edits, dead ends, variable naming choices) is potentially more identifying than a final answer alone and should be treated accordingly before any public data release.

**Data collected:** Code text per attempt, timestamp, test pass/fail state at each check, derived complexity/efficiency metrics.

**Status:** Under consideration

---

## 4. Per-challenge self-report of external resource use

**What:** After each challenge, ask participants to honestly report whether they used any external resources (e.g. Google, Stack Overflow, AI tools) to answer that specific question. A simple prompt along the lines of: "Did you look anything up for this one?" with a small set of honest-answer options (e.g. No / Googled it / Used AI / Used docs).

**Rationale:** Participants will realistically look things up. Rather than attempting to prevent or detect this, the study embraces the citizen-science model and relies on honest self-report -- consistent with how the approved post-session AI habits survey already works. The per-challenge granularity makes the data more analytically useful (resource use on hard vs easy problems, change in look-up behaviour over time, etc.).

**Why it may need an amendment:** The approved survey covers session-level AI habit self-report. A per-challenge resource-use question is the same methodology at finer granularity, so this is likely a minor addition. It should still be noted as a new instrument item.

**Data collected:** Per-challenge self-reported resource use category, linked to participant ID and challenge ID.

**Participant burden:** Minimal -- one question per challenge, a few seconds.

**Status:** Under consideration

---
