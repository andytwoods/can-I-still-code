"""Unit tests for tutorial_runner.py (the module the Pyodide worker also runs)."""

import importlib.util
from pathlib import Path

import pytest

RUNNER = Path(__file__).resolve().parents[2] / "static" / "tutorial" / "tutorial_runner.py"


@pytest.fixture(scope="module")
def runner():
    spec = importlib.util.spec_from_file_location("tutorial_runner", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(runner, code, reference, checks, params=None, seed=1, inject=False):
    return runner.run_task(code, reference, params or {}, inject, checks, seed, False)


VAR = [{"id": "x", "type": "variable", "name": "x"}]


class TestPlaceholders:
    def test_code_uses_repr_and_leaves_braces(self, runner):
        out = runner.substitute_code("d = {'a': 1}\nname = @@name@@\nprint(f'{name}')", {"name": "Bo"})
        assert out == "d = {'a': 1}\nname = 'Bo'\nprint(f'{name}')"

    def test_unknown_placeholder_raises(self, runner):
        with pytest.raises(runner.PlaceholderError):
            runner.substitute_code("x = @@nope@@", {})

    def test_call_args_are_resolved_and_copied(self, runner):
        params = {"xs": [1, 2]}
        args = runner.substitute_args(["@@xs@@", 3], params)
        args[0].append(99)
        assert params["xs"] == [1, 2]


class TestComparison:
    def test_bool_is_not_int(self, runner):
        assert not runner.values_equal(True, 1)
        assert not runner.values_equal(1, True)
        assert runner.values_equal(True, True)

    def test_float_tolerance(self, runner):
        assert runner.values_equal(0.1 + 0.2, 0.3)

    def test_lists_elementwise(self, runner):
        assert runner.values_equal([1, 2.0], [1, 2])
        assert not runner.values_equal([1, 2], [1, 2, 3])
        assert not runner.values_equal((1, 2), [1, 2])


class TestChecks:
    def test_variable_pass_and_fail(self, runner):
        assert run(runner, "x = 4", "x = 2 + 2", VAR)["passed"]
        res = run(runner, "x = 5", "x = 2 + 2", VAR)
        assert not res["passed"]
        assert res["checks"][0]["expected"] == "4"
        assert res["checks"][0]["actual"] == "5"

    def test_missing_variable_message(self, runner):
        res = run(runner, "y = 4", "x = 4", VAR)
        assert "couldn't find x" in res["checks"][0]["message"]

    def test_function_print_instead_of_return(self, runner):
        checks = [{"id": "f", "type": "function", "name": "f", "calls": [[2]]}]
        res = run(runner, "def f(a):\n    print(a * 2)", "def f(a):\n    return a * 2", checks)
        assert not res["passed"]
        assert "instead of using return" in res["checks"][0]["message"]

    def test_stdout_strip(self, runner):
        checks = [{"id": "o", "type": "stdout", "normalise": "strip"}]
        assert run(runner, "print('hi   ')\nprint()", "print('hi')", checks)["passed"]
        exact = [{"id": "o", "type": "stdout", "normalise": "exact"}]
        assert not run(runner, "print('hi   ')", "print('hi')", exact)["passed"]

    def test_no_error(self, runner):
        checks = [{"id": "ok", "type": "no_error"}]
        assert run(runner, "x = 1", "x = 1", checks)["passed"]
        assert not run(runner, "x = 1 / 0", "x = 1", checks)["passed"]

    def test_fresh_namespace_each_run(self, runner):
        run(runner, "leak = 1", "x = 1", VAR)
        res = run(runner, "x = leak", "x = 1", VAR)
        assert res["learner"]["error"]["type"] == "NameError"

    def test_injected_params_are_copies(self, runner):
        checks = [{"id": "xs", "type": "variable", "name": "xs"}]
        params = {"xs": [1, 2]}
        res = run(runner, "xs.append(3)", "xs.append(3)", checks, params=params, inject=True)
        assert res["passed"]
        assert params["xs"] == [1, 2]

    def test_randomness_is_reseeded_for_learner_and_reference(self, runner):
        code = "import random\nx = [random.randint(1, 6) for _ in range(5)]"
        assert run(runner, code, code, VAR, seed=3)["passed"]

    def test_function_calls_share_the_seeded_stream(self, runner):
        checks = [{"id": "f", "type": "function", "name": "roll", "calls": [[], [], []]}]
        code = "import random\ndef roll():\n    return random.randint(1, 6)"
        assert run(runner, code, code, checks, seed=5)["passed"]

    def test_input_is_blocked(self, runner):
        res = run(runner, "x = input('age?')", "x = 1", VAR)
        assert "input() isn't available" in res["learner"]["error"]["friendly"]


class TestOutput:
    def test_output_is_bounded(self, runner):
        res = run(runner, "for i in range(100000):\n    print('spam spam')\nx = 1", "x = 1", VAR)
        assert len(res["learner"]["stdout"]) < 10_100
        assert "cut off" in res["learner"]["stdout"]
        assert res["passed"]

    def test_streams_restored_after_error(self, runner):
        import sys  # noqa: PLC0415

        before = sys.stdout
        run(runner, "raise SystemExit", "x = 1", VAR)
        assert sys.stdout is before


class TestFriendlyErrors:
    @pytest.mark.parametrize(
        ("code", "needle"),
        [
            ("if True:\n\tx = 1\n        y = 2\n", "tabs and spaces"),
            ("for i in range(3)\n    pass", "colon"),
            ("x = undefined_thing", "doesn't know the name undefined_thing"),
            ("x = [1, 2][5]", "count from 0"),
            ("x = 1 / 0", "divided by zero"),
            ("x = 2.5 ^ 2", "use **"),
            ("def f():\n    pass\nf().append(1)", "forget to return"),
            ('print("hello"', "never closed"),
            ("x = true", "capital: True"),
            ("pritn('hi')", "Did you mean print"),
        ],
    )
    def test_messages(self, runner, code, needle):
        err = run(runner, code, "x = 1", VAR)["learner"]["error"]
        assert err is not None
        assert needle in err["friendly"]
        assert err["line"] is not None

    def test_caret_note_outside_strings(self, runner):
        res = run(runner, "x = 3 ^ 2  # '^' in a comment", "x = 1", VAR)
        assert res["learner"]["notes"]
        res = run(runner, "x = '3 ^ 2'  # ^ here too", "x = 1", VAR)
        assert not res["learner"]["notes"]


class TestGenerate:
    def test_generate_is_deterministic(self, runner):
        src = "def generate(rng):\n    return {'n': rng.randint(1, 1000)}"
        assert runner.generate(src, 4) == runner.generate(src, 4)

    def test_rejects_tuples(self, runner):
        with pytest.raises(TypeError):
            runner.generate("def generate(rng):\n    return {'p': (1, 2)}", 1)
