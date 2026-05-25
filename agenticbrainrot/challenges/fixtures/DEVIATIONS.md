# Fixture Deviations Log

All modifications to benchmark fixture files are recorded here per the scientific integrity policy in CLAUDE.md.

---

## DEV-001 — Labelled-array `expected` values in 5 HumanEval fixtures

**Root cause:** A batch of HumanEval fixtures were generated with a bug that embedded
the test-description string as the second element of the `expected` value, producing
`[scalar, "Test N"]` or `[scalar, "This prints if this assert fails …"]` instead of
a plain scalar. The HumanEval source uses plain integer/bool/float equality assertions;
the label is an incidental `assert` message from the original source, not part of the
expected return value.

Because the Pyodide test runner compared the function's scalar return value against a
list, every attempt on these challenges scored 0/N regardless of correctness. All
`ChallengeAttempt` records for these challenges before 2026-05-25 have been flagged
`data_quality_flag = "DEV-001"` and must be excluded from accuracy analysis (timing
data remains valid).

**Companion bug (DEV-001b):** The Pyodide worker detected which function to call by
regex-matching the *first* `def` in submitted code, ignoring `metadata.function_name`.
If a participant defined a helper before the main function the wrong function was called.
Fixed in the same commit by passing `metadata.function_name` explicitly to the worker.

**Date:** 2026-05-25  
**Approved by:** andytwoods

### Affected fixtures

| Fixture file | External ID | Source | HumanEval ID | Changed test cases |
|---|---|---|---|---|
| `d5/special-factorial-v1.json` | `special-factorial-v1` | HumanEval | humaneval-139 | All 4 |
| `d4/vowels-count-v1.json` | `vowels-count-v1` | HumanEval | humaneval-64 | All 5 |
| `d4/closest-integer-v1.json` | `closest-integer-v1` | HumanEval | humaneval-99 | All 5 |
| `d4/double-the-difference-v1.json` | `double-the-difference-v1` | HumanEval | humaneval-151 | All 5 |
| `d5/right-angle-triangle-v1.json` | `right-angle-triangle-v1` | HumanEval | humaneval-157 | Test 1 only |
| `d5/triangle-area-d5-v1.json` | `triangle-area-d5-v1` | HumanEval | humaneval-71 | Test 1 only |

### Change pattern (same for all)

**Original (example from `special-factorial-v1.json`):**
```json
{ "input": [4], "expected": [288, "Test 4"],         "description": "Test 1" }
{ "input": [5], "expected": [34560, "Test 5"],        "description": "Test 2" }
{ "input": [7], "expected": [125411328000, "Test 7"], "description": "Test 3" }
{ "input": [1], "expected": [1, "Test 1"],            "description": "Test 4" }
```

**Corrected:**
```json
{ "input": [4], "expected": 288,          "description": "Test 1" }
{ "input": [5], "expected": 34560,        "description": "Test 2" }
{ "input": [7], "expected": 125411328000, "description": "Test 3" }
{ "input": [1], "expected": 1,            "description": "Test 4" }
```
