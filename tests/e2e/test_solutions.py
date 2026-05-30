"""
End-to-end tests: verify that every challenge's reference_solution passes all
test cases when executed inside the browser's Pyodide runtime.

Run against a running dev server:
    uv run pytest tests/e2e/ -m e2e --base-url http://localhost:8000

Parallel (faster):
    uv run pytest tests/e2e/ -m e2e --base-url http://localhost:8000 -n 4
"""

import json
import time
from pathlib import Path

import pytest
from playwright.sync_api import expect

FIXTURE_ROOT = Path(__file__).parent.parent.parent / "agenticbrainrot/challenges/fixtures"

PYODIDE_READY_TIMEOUT = 120_000  # ms – generous for first WASM download
RUN_RESULT_TIMEOUT = 60_000      # ms – per-challenge execution + efficiency timing
RUN_TIME_LIMIT_S = 8             # seconds – wall-clock limit for run + efficiency timing


def _load_challenge_params():
    # Use a dict so that when multiple fixture files share an external_id,
    # the last one (highest tier directory, sorted) wins — matching the
    # behaviour of sync_fixture_test_cases which also processes in sorted order.
    by_eid: dict = {}
    for path in sorted(FIXTURE_ROOT.rglob("*.json")):
        if path.name == "clarifications.json":
            continue
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        eid = data.get("external_id")
        ref = data.get("reference_solution", "").strip()
        test_cases = data.get("test_cases", [])
        if not data.get("is_active", True):
            continue
        if eid and ref and test_cases:
            by_eid[eid] = (eid, ref, len(test_cases))
    return [pytest.param(*v, id=v[0]) for v in by_eid.values()]


CHALLENGE_PARAMS = _load_challenge_params()


@pytest.mark.e2e
@pytest.mark.parametrize("external_id,reference_solution,expected_count", CHALLENGE_PARAMS)
def test_reference_solution_passes(page, base_url, external_id, reference_solution, expected_count):
    page.goto(f"{base_url}/challenges/preview/{external_id}/")

    # Wait for Pyodide to initialise (run button becomes enabled)
    run_btn = page.locator("#run-btn")
    expect(run_btn).to_be_enabled(timeout=PYODIDE_READY_TIMEOUT)

    # Replace skeleton code with the reference solution via CodeMirror 5's JS API
    page.evaluate(
        """(code) => {
            const wrapper = document.querySelector('#code-editor .CodeMirror');
            if (wrapper && wrapper.CodeMirror) {
                wrapper.CodeMirror.setValue(code);
            }
        }""",
        reference_solution,
    )

    # Inject reference-solution-data so the worker can compute efficiency_ratio.
    # The preview template omits this (only session views include it), so we
    # inject it here to exercise the full timing pipeline.
    page.evaluate(
        """(ref) => {
            let el = document.getElementById('reference-solution-data');
            if (!el) {
                el = document.createElement('script');
                el.id = 'reference-solution-data';
                el.type = 'application/json';
                document.body.appendChild(el);
            }
            el.textContent = JSON.stringify(ref);
        }""",
        reference_solution,
    )

    # Clear any stale results then run
    page.evaluate("""() => {
        const tp = document.getElementById('tests-passed');
        if (tp) tp.value = '';
        const tr = document.getElementById('test-results-summary');
        if (tr) tr.remove();
    }""")
    t0 = time.time()
    run_btn.click()

    # Wait until results land (tests-passed hidden input is populated)
    page.wait_for_function(
        "() => { const el = document.getElementById('tests-passed'); return el && el.value !== ''; }",
        timeout=RUN_RESULT_TIMEOUT,
    )
    elapsed = time.time() - t0
    assert elapsed < RUN_TIME_LIMIT_S, (
        f"{external_id}: run took {elapsed:.1f}s (limit {RUN_TIME_LIMIT_S}s) – "
        "consider reducing measure_median_us samples or timeout_s"
    )

    passed = int(page.locator("#tests-passed").input_value())
    total = int(page.locator("#tests-total").input_value())

    assert total == expected_count, (
        f"{external_id}: fixture has {expected_count} test cases but browser ran {total}"
    )
    assert passed == total, (
        f"{external_id}: {passed}/{total} tests passed – reference solution failed"
    )

    # Verify efficiency ratio was computed (non-empty data attribute on summary)
    summary = page.locator("#test-results-summary")
    efficiency = summary.get_attribute("data-efficiency-ratio")
    assert efficiency not in (None, ""), (
        f"{external_id}: efficiency_ratio was not computed (got {efficiency!r})"
    )

    # Verify complexity metrics were computed
    complexity = summary.get_attribute("data-complexity-computed")
    assert complexity == "true", (
        f"{external_id}: complexity metrics were not computed"
    )
