"""
End-to-end tests for the browser Python tutorial at /tutorial/.

Run against a running dev server:
    uv run pytest tests/e2e/test_tutorial.py -m e2e --base-url http://localhost:8000
"""

import json
import re
from pathlib import Path
from urllib.parse import urlparse

import pytest
from playwright.sync_api import expect

BUNDLE = Path(__file__).parent.parent.parent / "agenticbrainrot/static/tutorial/bank.bundle.json"
PYODIDE_READY_TIMEOUT = 120_000
RESULT_TIMEOUT = 30_000
PLOT_TIMEOUT = 120_000

pytestmark = pytest.mark.e2e


def _bank():
    return json.loads(BUNDLE.read_text())


def _fresh(page, base_url):
    # Clear storage from a same-origin page that does not run the tutorial: the tutorial saves
    # its state on pagehide, which would undo a clear made from the tutorial page itself.
    page.goto(f"{base_url}/static/tutorial/tutorial.css")
    page.evaluate("() => { try { localStorage.removeItem('tutorial_v1'); } catch (e) {} }")
    page.goto(f"{base_url}/tutorial/")
    expect(page.locator("#run-btn")).to_be_enabled(timeout=PYODIDE_READY_TIMEOUT)


def _open(page, task_id):
    """Open a task through the UI's own navigation (block, then tab)."""
    page.evaluate(
        """(id) => {
            const st = window.__tutorial.state;
            const t = window.__tutorial.bank.tasks[id];
            st.current.block = t.block; st.current.taskId = id;
            localStorage.setItem('tutorial_v1', JSON.stringify(st));
        }""",
        task_id,
    )
    page.reload()
    expect(page.locator("#run-btn")).to_be_enabled(timeout=PYODIDE_READY_TIMEOUT)


def _set_code(page, code):
    page.evaluate("(c) => window.__tutorial.setCode(c)", code)


def _run(page):
    page.locator("#run-btn").click()
    expect(page.locator("#run-btn")).to_be_enabled(timeout=RESULT_TIMEOUT)


def _solution(page, task_id):
    """The reference with this variant's values filled in, via the hint/solution path."""
    return page.evaluate(
        """(id) => {
            const t = window.__tutorial.bank.tasks[id];
            const reprs = window.__tutorial.state.tasks[id] && window.__tutorial.variantReprs();
            return t.reference.replace(/@@([A-Za-z_][A-Za-z0-9_]*)@@/g, (m, n) => reprs[n]);
        }""",
        task_id,
    )


def test_pyodide_becomes_ready(page, base_url):
    _fresh(page, base_url)
    expect(page.locator("#py-status")).to_contain_text("ready")


def test_solve_block2_task_and_reload_restores(page, base_url):
    _fresh(page, base_url)
    _open(page, "b2-avg-L4")
    code = _solution(page, "b2-avg-L4") + "# mine\n"
    _set_code(page, code)
    _run(page)
    expect(page.locator("#results")).to_contain_text("Passed")
    page.reload()
    expect(page.locator("#run-btn")).to_be_enabled(timeout=PYODIDE_READY_TIMEOUT)
    assert "# mine" in page.evaluate("() => window.__tutorial.getCode()")
    state = page.evaluate("() => window.__tutorial.state")
    assert state["tasks"]["b2-avg-L4"]["everPassed"] is True


def test_new_example_changes_the_numbers(page, base_url):
    _fresh(page, base_url)
    _open(page, "b2-avg-L4")
    before = page.locator("#task-prompt").inner_text() + page.evaluate("() => window.__tutorial.getCode()")
    changed = False
    for _ in range(3):  # two seeds could, very rarely, give the same list
        page.locator("#new-btn").click()
        expect(page.locator("#new-btn")).to_be_enabled(timeout=RESULT_TIMEOUT)
        after = page.locator("#task-prompt").inner_text() + page.evaluate("() => window.__tutorial.getCode()")
        if after != before:
            changed = True
            break
    assert changed


def test_infinite_loop_times_out_and_restarts(page, base_url):
    _fresh(page, base_url)
    _open(page, "b2-avg-L4")
    _set_code(page, "while True:\n    pass\n")
    page.locator("#run-btn").click()
    expect(page.locator("#results")).to_contain_text("took too long", timeout=RESULT_TIMEOUT)
    expect(page.locator("#run-btn")).to_be_enabled(timeout=PYODIDE_READY_TIMEOUT)
    assert "while True" in page.evaluate("() => window.__tutorial.getCode()")
    _set_code(page, "x = 1\n")
    _run(page)
    expect(page.locator("#results")).to_contain_text("FAIL")
    expect(page.locator("#results")).not_to_contain_text("took too long")


def test_tab_space_mix_gives_friendly_message(page, base_url):
    _fresh(page, base_url)
    _open(page, "b2-avg-L4")
    _set_code(page, "if True:\n\tx = 1\n        y = 2\n")
    _run(page)
    expect(page.locator("#results")).to_contain_text("tabs and spaces")


def test_core_plot_task_shows_image(page, base_url):
    plot_tasks = [t for t in _bank()["tasks"].values() if t.get("allow_plot")]
    if not plot_tasks:
        pytest.skip("no plotting task in the bank yet")
    t = plot_tasks[0]
    _fresh(page, base_url)
    _open(page, t["id"])
    _set_code(page, _solution(page, t["id"]))
    page.locator("#run-btn").click()
    expect(page.locator("#plots img")).to_have_count(1, timeout=PLOT_TIMEOUT)
    expect(page.locator("#results")).to_contain_text("Passed")


def _sample_ids():
    tasks = _bank()["tasks"]
    ids = sorted(tasks)
    # A spread across blocks and kinds, without plotting tasks (covered above).
    picked, seen = [], set()
    for tid in ids:
        t = tasks[tid]
        key = (t["block"], t["kind"])
        if key in seen or t.get("allow_plot"):
            continue
        seen.add(key)
        picked.append(tid)
    return picked[:5] if len(picked) >= 5 else ids[:5]


@pytest.mark.parametrize("task_id", _sample_ids())
def test_reference_passes_in_real_worker(page, base_url, task_id):
    _fresh(page, base_url)
    _open(page, task_id)
    _set_code(page, _solution(page, task_id))
    _run(page)
    expect(page.locator("#results")).to_contain_text("Passed")


def test_no_backend_hits_after_first_load(page, base_url):
    app_origin = urlparse(base_url).netloc
    seen = []
    page.on("request", lambda req: seen.append(req.url))
    _fresh(page, base_url)
    seen.clear()  # everything up to here is "the initial page load"
    page.reload()
    expect(page.locator("#run-btn")).to_be_enabled(timeout=PYODIDE_READY_TIMEOUT)
    first_load_page = [u for u in seen if urlparse(u).path == "/tutorial/"]
    assert len(first_load_page) == 1
    seen.clear()
    _open(page, "b2-avg-L4")
    seen.clear()
    # Use the page: run, fail, hint, new example, next, rating, navigation.
    _set_code(page, "average = 0\n")
    _run(page)
    _run(page)
    page.locator("#hint-btn").click()
    page.locator("#solution-btn").click()
    page.locator("#new-btn").click()
    expect(page.locator("#new-btn")).to_be_enabled(timeout=RESULT_TIMEOUT)
    page.locator("#next-btn").click()
    expect(page.locator("#run-btn")).to_be_enabled(timeout=RESULT_TIMEOUT)
    page.locator("#block-list a").nth(1).click()
    page.locator("#block-list a").last.click()
    page.evaluate("() => window.dispatchEvent(new Event('pagehide'))")
    app_hits = [u for u in seen if urlparse(u).netloc == app_origin and not urlparse(u).path.startswith("/static/")]
    assert app_hits == [], app_hits
    assert not [u for u in seen if re.search(r"rollbar", u)]


def _state(page):
    return page.evaluate("() => window.__tutorial.state")


def _solve_current(page, task_id):
    _set_code(page, _solution(page, task_id))
    _run(page)
    expect(page.locator("#results")).to_contain_text("Passed")


def test_check_task_pass_marks_block_done_and_ladder_starts_at_3(page, base_url):
    _fresh(page, base_url)
    _open(page, "b2-check")
    _solve_current(page, "b2-check")
    st = _state(page)
    assert st["blocks"]["2"]["done"] is True
    assert st["blocks"]["2"]["checkPassed"] is True
    assert st["ladders"]["2"]["level"] == 3
    expect(page.locator("#block-list a").nth(1)).to_contain_text("✓")


def test_failed_check_task_offers_core_tasks(page, base_url):
    _fresh(page, base_url)
    _open(page, "b2-check")
    _set_code(page, "total = 0\n")
    _run(page)
    expect(page.locator("#check-failed-note")).to_be_visible()
    page.locator("#to-core-btn").click()
    expect(page.locator("#task-kind")).to_have_text("Core task")


def test_hint_after_one_fail_solution_after_two(page, base_url):
    _fresh(page, base_url)
    _open(page, "b2-avg-L4")
    expect(page.locator("#hint-btn")).to_be_disabled()
    _set_code(page, "average = 0\n")
    _run(page)
    expect(page.locator("#hint-btn")).to_be_enabled()
    expect(page.locator("#solution-btn")).to_be_disabled()
    _run(page)
    expect(page.locator("#solution-btn")).to_be_enabled()
    page.locator("#solution-btn").click()
    expect(page.locator("#solution-code")).to_contain_text("average = sum(week) / len(week)")


def _practice_level(page):
    return _state(page)["ladders"]["2"]["level"]


def _next(page):
    page.locator("#next-btn").click()
    expect(page.locator("#run-btn")).to_be_enabled(timeout=RESULT_TIMEOUT)


def test_staircase_moves_on_next(page, base_url):
    _fresh(page, base_url)
    _open(page, "b2-read-L1")
    page.locator("#task-tabs a", has_text="Practice").click()
    expect(page.locator("#run-btn")).to_be_enabled(timeout=RESULT_TIMEOUT)
    assert _practice_level(page) == 1
    # passed + "too easy" -> +2
    tid = _state(page)["current"]["taskId"]
    _solve_current(page, tid)
    expect(page.locator("#rating")).to_be_visible()
    page.locator("#rating [data-rating='too_easy']").click()
    _next(page)
    assert _practice_level(page) == 3
    # skipped without running -> same
    _next(page)
    assert _practice_level(page) == 3
    # failed -> -1
    _set_code(page, "x = 0\n")
    _run(page)
    _next(page)
    assert _practice_level(page) == 2
    # two "just right" passes in a row -> +1 on the second
    for expected in (2, 3):
        tid = _state(page)["current"]["taskId"]
        _solve_current(page, tid)
        page.locator("#rating [data-rating='just_right']").click()
        _next(page)
        assert _practice_level(page) == expected
    # solution viewed counts as -1 even if passed
    tid = _state(page)["current"]["taskId"]
    _set_code(page, "x = 0\n")
    _run(page)
    _run(page)
    page.locator("#solution-btn").click()
    _solve_current(page, tid)
    expect(page.locator("#rating")).to_be_hidden()
    _next(page)
    assert _practice_level(page) == 2
