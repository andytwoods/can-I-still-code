# Project Instructions (Claude)

IMPORTANT:
- Before making any code changes, read and follow: `.junie/guidelines.md`
- If there is any conflict, `.junie/guidelines.md` is the source of truth.

## Project-Specific Rules

### Challenge Fixtures - Scientific Integrity

Challenge fixtures in `challenges/fixtures/` are derived from **published research datasets** (MBPP, HumanEval, etc.). They are research instruments, not ordinary application data.

#### Rules
- **Never edit a fixture file directly.** Descriptions, test cases, skeleton code, and metadata must remain faithful to the original published source so results are reproducible and comparable to prior literature.
- **All deviations must be logged.** If a challenge description is ambiguous, a test case is incorrect, or any modification is genuinely necessary, it must be recorded in a structured deviation log (e.g. `challenges/fixtures/DEVIATIONS.md`) with:
  - The fixture file and `external_id` affected.
  - What was changed and why.
  - The original value (verbatim).
  - The new value.
  - Who approved the change and the date.
- **Prefer additive changes over edits.** If extra context is needed (e.g. a clarifying example), add a `"clarification"` field to the fixture JSON or display supplementary text in the UI - do not overwrite the original `"description"`.
- **Attribute the source.** Every fixture must retain its `source` block (dataset, paper citation, license, repository, dataset_id).

#### Rationale
This study measures coding skill using standardised problems. If we silently alter those problems, our results become incomparable to other studies using the same benchmarks, and reviewers or replicators cannot verify what participants actually saw.
