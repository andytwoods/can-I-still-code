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

---

## DEV-002 — Labelled-array `expected` values in 2 further HumanEval fixtures

Same root cause as DEV-001. Two fixtures were missed in the initial batch fix.

**Date:** 2026-05-30  
**Approved by:** andytwoods

| Fixture file | External ID | HumanEval ID | Changed test cases |
|---|---|---|---|
| `d5/circular-shift-v1.json` | `circular-shift-v1` | humaneval-65 | TC4, TC5 |
| `d5/generate-integers-v1.json` | `generate-integers-v1` | humaneval-163 | All 4 |

### Change pattern

**Original (`circular-shift-v1.json` TC4 and TC5):**
```json
{ "input": [12, 1],   "expected": ["21", "This prints if this assert fails 1 (good for debugging!)"] }
{ "input": [11, 101], "expected": ["11", "This prints if this assert fails 2 (also good for debugging!)"] }
```

**Corrected:**
```json
{ "input": [12, 1],   "expected": "21" }
{ "input": [11, 101], "expected": "11" }
```

**Original (`generate-integers-v1.json`, all 4 TCs):**
```json
{ "input": [2, 10],   "expected": [[2, 4, 6, 8], "Test 1"] }
{ "input": [10, 2],   "expected": [[2, 4, 6, 8], "Test 2"] }
{ "input": [132, 2],  "expected": [[2, 4, 6, 8], "Test 3"] }
{ "input": [17, 89],  "expected": [[], "Test 4"] }
```

**Corrected:**
```json
{ "input": [2, 10],   "expected": [2, 4, 6, 8] }
{ "input": [10, 2],   "expected": [2, 4, 6, 8] }
{ "input": [132, 2],  "expected": [2, 4, 6, 8] }
{ "input": [17, 89],  "expected": [] }
```

---

## DEV-003 — Broken reference solution in `remove-similar-row-v1`

The original MBPP reference solution attempted `set(sub)` where each `sub` is a list of
`[int, int]` pairs, crashing with `unhashable type: 'list'`. The solution also returned a
`set` of tuples rather than the list-of-lists the test cases expect.

**Date:** 2026-05-30  
**Approved by:** andytwoods

| Fixture file | External ID | Source | MBPP ID |
|---|---|---|---|
| `d3/remove-similar-row-v1.json` | `remove-similar-row-v1` | MBPP | mbpp-642 |

**Original `reference_solution`:**
```python
def remove_similar_row(test_list):
  res = set(sorted([tuple(sorted(set(sub))) for sub in test_list]))
  return (res)
```

**Corrected `reference_solution`:**
```python
def remove_similar_row(test_list):
    seen = set()
    result = []
    for sub in test_list:
        key = frozenset(map(tuple, sub))
        if key not in seen:
            seen.add(key)
            result.append(sorted(sub))
    return sorted(result)
```

The corrected solution uses `frozenset(map(tuple, sub))` to build a hashable key from each
row, deduplicates while preserving the canonical sorted form of each surviving row, and
returns a sorted list-of-lists matching the expected output type.
