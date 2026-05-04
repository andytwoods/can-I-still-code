# Project Instructions (Claude)

IMPORTANT:
- Before making any code changes, read and follow: `.junie/guidelines.md`
- If there is any conflict, `.junie/guidelines.md` is the source of truth.

## Project-Specific Rules

### Challenge Fixtures - Scientific Integrity

There are two distinct types of challenges in this project:

#### 1. Benchmark fixtures (`challenges/fixtures/`, `type: "benchmark"`)
Derived from **published research datasets** (MBPP, HumanEval, etc.). These are research instruments and must be treated strictly.

- **Never edit a fixture file directly.** Descriptions, test cases, skeleton code, and metadata must remain faithful to the original published source so results are reproducible and comparable to prior literature.
- **All deviations must be logged.** If a challenge description is ambiguous, a test case is incorrect, or any modification is genuinely necessary, it must be recorded in a structured deviation log (e.g. `challenges/fixtures/DEVIATIONS.md`) with:
  - The fixture file and `external_id` affected.
  - What was changed and why.
  - The original value (verbatim).
  - The new value.
  - Who approved the change and the date.
- **Prefer additive changes over edits.** If extra context is needed (e.g. a clarifying example), add a `"clarification"` field to the fixture JSON or display supplementary text in the UI - do not overwrite the original `"description"`.
- **Attribute the source.** Every fixture must retain its `source` block (dataset, paper citation, license, repository, dataset_id).

#### 2. Screening / pilot fixtures (`d0/`, `type: "screening"`)
Short, simple everyday-Python problems (e.g. "sort a list", "count vowels") stored in `agenticbrainrot/challenges/fixtures/d0/`. Used as a separate level-0 study arm. These are **not** drawn from published benchmarks and are **never mixed** with benchmark data in analysis. They may include written and multiple-choice feedback questions alongside the code challenge. These fixtures can be created and edited freely, but must carry `"type": "screening"` in their metadata so they are always distinguishable from benchmark fixtures.

#### Rationale
Benchmark fixtures must remain unaltered so results are comparable to prior literature. Screening fixtures are a separate instrument; keeping them clearly typed prevents accidental contamination of the main longitudinal dataset.
