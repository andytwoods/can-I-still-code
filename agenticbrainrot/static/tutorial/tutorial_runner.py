"""Task runner for the browser Python tutorial.

One module, two hosts:

* the Pyodide worker (``tutorial-worker.js``) fetches this file as a static
  asset and calls :func:`generate_json` / :func:`run_task_json`;
* the bank builder (``scripts/build_tutorial_bank.py``) imports it under
  CPython to validate every template.

Sharing the code means the validator checks tasks with exactly the rules the
learner's browser applies. Keep it to the standard library (plus matplotlib,
imported lazily for plotting tasks).
"""

from __future__ import annotations

import base64
import copy
import io
import json
import math
import random
import re
import sys
import tokenize
import traceback

PLACEHOLDER = re.compile(r"@@([A-Za-z_][A-Za-z0-9_]*)@@")
LEARNER_FILENAME = "<your code>"
OUTPUT_LIMIT = 10_000
DEFAULT_ABS_TOL = 1e-9
DEFAULT_REL_TOL = 1e-9


# ── placeholders ─────────────────────────────────────────────────────────────


class PlaceholderError(KeyError):
    pass


def substitute_code(text: str, params: dict) -> str:
    """Replace ``@@name@@`` with ``repr(value)``. Braces are left alone."""

    def repl(match):
        name = match.group(1)
        if name not in params:
            raise PlaceholderError(name)
        return repr(params[name])

    return PLACEHOLDER.sub(repl, text or "")


def display_value(value) -> str:
    """Text shown in a prompt for a parameter: strings bare, the rest as Python."""
    return value if isinstance(value, str) else repr(value)


def substitute_args(value, params: dict):
    """Resolve ``"@@name@@"`` strings anywhere inside a call's argument list."""
    if isinstance(value, str):
        match = PLACEHOLDER.fullmatch(value)
        if match:
            name = match.group(1)
            if name not in params:
                raise PlaceholderError(name)
            return copy.deepcopy(params[name])
        return value
    if isinstance(value, list):
        return [substitute_args(v, params) for v in value]
    if isinstance(value, dict):
        return {k: substitute_args(v, params) for k, v in value.items()}
    return value


# ── generation ───────────────────────────────────────────────────────────────


def _json_compatible(value) -> bool:
    try:
        return json.loads(json.dumps(value)) == value
    except (TypeError, ValueError):
        return False


def generate(generator_src: str | None, seed: int) -> dict:
    if not generator_src:
        return {}
    ns: dict = {"__name__": "__tutorial_generator__"}
    exec(compile(generator_src, "<generator>", "exec"), ns, ns)  # noqa: S102 - reviewed bank code
    params = ns["generate"](random.Random(seed))
    if not isinstance(params, dict):
        msg = "generate() must return a dict"
        raise TypeError(msg)
    if not _json_compatible(params):
        msg = "generate() must return JSON-compatible values (lists, not tuples)"
        raise TypeError(msg)
    return params


def generate_json(request_json: str) -> str:
    req = json.loads(request_json)
    try:
        params = generate(req.get("generatorSrc"), int(req.get("seed", 0)))
    except Exception as exc:  # noqa: BLE001 - reported back to the page, never swallowed
        return json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
    display = {k: display_value(v) for k, v in params.items()}
    reprs = {k: repr(v) for k, v in params.items()}
    return json.dumps({"ok": True, "params": params, "display": display, "reprs": reprs})


# ── bounded output capture ───────────────────────────────────────────────────


class BoundedWriter(io.TextIOBase):
    """Keeps at most ``limit`` characters; anything later is dropped at once."""

    def __init__(self, limit: int = OUTPUT_LIMIT):
        super().__init__()
        self.limit = limit
        self.parts: list[str] = []
        self.size = 0
        self.truncated = False

    def writable(self):
        return True

    def write(self, s):
        if not isinstance(s, str):
            s = str(s)
        room = self.limit - self.size
        if room <= 0:
            if s:
                self.truncated = True
            return len(s)
        if len(s) > room:
            self.truncated = True
        kept = s[:room]
        self.parts.append(kept)
        self.size += len(kept)
        return len(s)

    def getvalue(self) -> str:
        text = "".join(self.parts)
        if self.truncated:
            text += "\n… (output cut off after 10,000 characters)"
        return text


def _no_input(*_args, **_kwargs):
    msg = "input() isn't available in this tutorial. Set the value directly instead, e.g. age = 30"
    raise RuntimeError(msg)


# ── friendly errors ──────────────────────────────────────────────────────────


def _learner_lineno(exc: BaseException) -> int | None:
    if isinstance(exc, SyntaxError) and exc.filename == LEARNER_FILENAME:
        return exc.lineno
    line = None
    for frame, lineno in traceback.walk_tb(exc.__traceback__):
        if frame.f_code.co_filename == LEARNER_FILENAME:
            line = lineno
    return line


def _last_line(exc: BaseException) -> str:
    return traceback.format_exception_only(type(exc), exc)[-1].strip()


def caret_lines(code: str) -> list[int]:
    """Lines where ``^`` is used as an operator (not inside strings or comments)."""
    lines = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            if tok.type == tokenize.OP and tok.string in ("^", "^="):
                lines.append(tok.start[0])
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return lines


def explain(exc: BaseException, code: str = "") -> str:
    name = type(exc).__name__
    text = str(exc)
    if isinstance(exc, (IndentationError, TabError)):
        if "expected an indented block" in text:
            return (
                "A line ending in a colon (:) must be followed by at least one indented line. "
                "Indent the next line by 4 spaces."
            )
        if "unexpected indent" in text:
            return (
                "This line is indented, but nothing above it opens a block. "
                "Python uses indentation to see which lines belong together; remove the extra spaces."
            )
        return (
            "Python uses indentation to see which lines belong together. Check this line uses 4 spaces, "
            "and that tabs and spaces are not mixed (common after pasting)."
        )
    if isinstance(exc, SyntaxError):
        if "expected ':'" in text:
            return "Lines starting with for, if, elif, else, while or def must end with a colon (:)."
        if "was never closed" in text or "unexpected EOF" in text:
            return "A bracket or quote mark is opened but never closed. Count your ( ) [ ] and quote marks."
        if "unterminated string" in text:
            return "A piece of text is missing its closing quote mark. Text needs a quote at both ends."
        if "Maybe you meant '==' or ':=' instead of '='" in text or "cannot assign to" in text:
            return "= stores a value; == compares two values. Inside an if, use ==."
        if "invalid syntax" in text and re.search(r"\belse\s+if\b", code):
            return "Python writes 'else if' as elif."
        return "Python couldn't read this line. Look for a missing bracket, quote mark, colon or comma near it."
    if isinstance(exc, NameError):
        match = re.search(r"name '([^']+)' is not defined", text)
        missing = match.group(1) if match else "this name"
        hint = (
            f"Python doesn't know the name {missing}. Check the spelling and capitals, "
            "and that the line defining it ran first."
        )
        if missing in ("true", "false", "none"):
            hint += f" Python writes it with a capital: {missing.capitalize()}."
        elif missing == "pritn":
            hint += " Did you mean print?"
        return hint
    if isinstance(exc, TypeError) and "^" in text:
        return "^ is not 'to the power of' in Python; use ** (so 3 squared is 3 ** 2)."
    if isinstance(exc, TypeError) and "NoneType" in text:
        return "Something here is None (no value). Did a function forget to return, or did you store the result of .append()?"
    if isinstance(exc, IndexError):
        return "That position isn't in the list. Lists count from 0, so the last item of 5 is at position 4."
    if isinstance(exc, ZeroDivisionError):
        return "You divided by zero. Check the number after the / is not 0 (an empty list has len 0)."
    if isinstance(exc, AttributeError) and "'NoneType'" in text:
        return "Something here is None (no value). Did a function forget to return?"
    if isinstance(exc, ModuleNotFoundError) and "matplotlib" in text:
        return "Plotting is only switched on in the plotting tasks."
    if isinstance(exc, RuntimeError) and "input()" in text:
        return text
    return f"Python stopped with a {name}. Read the last line of the message: it names the problem."


def describe_error(exc: BaseException, code: str = "") -> dict:
    return {
        "type": type(exc).__name__,
        "last_line": _last_line(exc),
        "line": _learner_lineno(exc),
        "friendly": explain(exc, code),
    }


# ── plots ────────────────────────────────────────────────────────────────────


class _PlotCapture:
    def __init__(self, enabled: bool):
        self.enabled = enabled
        self.images: list[str] = []
        self.plt = None
        self._orig_show = None

    def __enter__(self):
        if not self.enabled:
            return self
        import matplotlib  # noqa: PLC0415 - loaded only for plotting tasks

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # noqa: PLC0415

        self.plt = plt
        self._orig_show = plt.show
        plt.show = self._show
        return self

    def _show(self, *_args, **_kwargs):
        plt = self.plt
        for num in plt.get_fignums():
            fig = plt.figure(num)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=80, bbox_inches="tight")
            self.images.append(base64.b64encode(buf.getvalue()).decode("ascii"))
        plt.close("all")

    def collect_unshown(self):
        if self.plt is not None and self.plt.get_fignums():
            self._show()

    def __exit__(self, *exc):
        if self.plt is not None:
            self.plt.close("all")
            self.plt.show = self._orig_show
        elif "matplotlib.pyplot" in sys.modules:
            sys.modules["matplotlib.pyplot"].close("all")
        return False


# ── one evaluation (code + its function-check calls) ─────────────────────────


class _Missing:
    pass


MISSING = _Missing()


def evaluate(code: str, params: dict, inject_params: bool, checks: list, seed: int, allow_plot: bool) -> dict:
    """Run ``code`` in a fresh namespace, then every function-check call, in order."""
    ns: dict = {"__name__": "__main__", "__builtins__": __builtins__, "input": _no_input}
    if inject_params:
        ns.update(copy.deepcopy(params))
    out, err = BoundedWriter(), BoundedWriter()
    old_out, old_err = sys.stdout, sys.stderr
    result = {"ns": ns, "error": None, "calls": {}, "stdout": "", "stderr": "", "plots": []}
    plots = _PlotCapture(allow_plot)
    random.seed(seed)
    sys.stdout, sys.stderr = out, err
    try:
        with plots:
            try:
                exec(compile(code, LEARNER_FILENAME, "exec"), ns, ns)  # noqa: S102 - the point of the tool
            except BaseException as exc:  # noqa: BLE001 - learner code may raise anything, incl. SystemExit
                if isinstance(exc, KeyboardInterrupt):
                    raise
                result["error"] = describe_error(exc, code)
            if result["error"] is None:
                for check in checks:
                    if check.get("type") != "function":
                        continue
                    fn = ns.get(check["name"], MISSING)
                    outcomes = []
                    for call in check.get("calls", []):
                        args = copy.deepcopy(substitute_args(call, params))
                        if fn is MISSING or not callable(fn):
                            outcomes.append(("missing", None))
                            continue
                        try:
                            outcomes.append(("ok", fn(*args)))
                        except BaseException as exc:  # noqa: BLE001
                            if isinstance(exc, KeyboardInterrupt):
                                raise
                            outcomes.append(("error", describe_error(exc, code)))
                    result["calls"][check["id"]] = outcomes
            plots.collect_unshown()
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    result["stdout"] = out.getvalue()
    result["stderr"] = err.getvalue()
    result["plots"] = plots.images
    return result


# ── comparison ───────────────────────────────────────────────────────────────


def values_equal(actual, expected, abs_tol=DEFAULT_ABS_TOL, rel_tol=DEFAULT_REL_TOL) -> bool:
    if isinstance(expected, bool) or isinstance(actual, bool):
        return isinstance(expected, bool) and isinstance(actual, bool) and actual == expected
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if math.isnan(expected) or math.isnan(actual):
            return math.isnan(expected) and math.isnan(actual)
        return math.isclose(actual, expected, abs_tol=abs_tol, rel_tol=rel_tol)
    if isinstance(expected, (list, tuple)):
        return (
            type(actual) is type(expected)
            and len(actual) == len(expected)
            and all(values_equal(a, e, abs_tol, rel_tol) for a, e in zip(actual, expected, strict=True))
        )
    if isinstance(expected, dict):
        return (
            isinstance(actual, dict)
            and actual.keys() == expected.keys()
            and all(values_equal(actual[k], expected[k], abs_tol, rel_tol) for k in expected)
        )
    try:
        return bool(actual == expected)
    except Exception:  # noqa: BLE001 - odd learner objects with a broken __eq__
        return False


def show(value, limit: int = 300) -> str:
    try:
        text = repr(value)
    except Exception:  # noqa: BLE001
        text = f"<{type(value).__name__}>"
    return text if len(text) <= limit else text[:limit] + "…"


def normalise_stdout(text: str, mode: str) -> str:
    if mode == "exact":
        return text
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    return "\n".join(lines).strip("\n")


def _call_text(name: str, call: list, params: dict) -> str:
    try:
        args = substitute_args(call, params)
    except PlaceholderError:
        args = call
    return f"{name}({', '.join(show(a, 80) for a in args)})"


def _none_hint(actual, expected) -> str:
    if actual is None and expected is not None:
        return " Your answer is None – did a function forget to return, or did you store the result of .append()?"
    return ""


def compare(check: dict, learner: dict, reference: dict, params: dict) -> dict:
    cid = check["id"]
    ctype = check["type"]
    abs_tol = check.get("abs_tol", DEFAULT_ABS_TOL)
    rel_tol = check.get("rel_tol", DEFAULT_REL_TOL)
    res = {"id": cid, "type": ctype, "passed": False, "expected": "", "actual": "", "message": ""}

    if reference["error"] is not None:
        res["message"] = "The reference solution failed – this task has a bug. Please tell the organiser."
        res["actual"] = reference["error"]["last_line"]
        return res

    if ctype == "no_error":
        res["passed"] = learner["error"] is None
        res["expected"] = "no error"
        res["actual"] = "no error" if res["passed"] else learner["error"]["last_line"]
        res["message"] = "Your code ran without an error." if res["passed"] else "Your code stopped with an error."
        return res

    if ctype == "stdout":
        mode = check.get("normalise", "strip")
        exp, act = normalise_stdout(reference["stdout"], mode), normalise_stdout(learner["stdout"], mode)
        res["expected"], res["actual"] = exp, act
        res["passed"] = learner["error"] is None and exp == act
        if learner["error"] is not None:
            res["message"] = "Your code stopped with an error before it finished printing."
        elif res["passed"]:
            res["message"] = "Printed output matches."
        elif not act:
            res["message"] = "Your code didn't print anything. Use print(...) to show a value."
        else:
            res["message"] = "Printed output is different. Compare it line by line."
        return res

    if learner["error"] is not None:
        res["message"] = "Your code stopped with an error, so this couldn't be checked yet."
        return res

    if ctype == "variable":
        name = check["name"]
        exp = reference["ns"].get(name, MISSING)
        act = learner["ns"].get(name, MISSING)
        res["expected"] = show(exp)
        if act is MISSING:
            res["actual"] = "(not defined)"
            res["message"] = f"I couldn't find {name} – did you store your answer under that name?"
            return res
        res["actual"] = show(act)
        res["passed"] = values_equal(act, exp, abs_tol, rel_tol)
        res["message"] = (
            f"{name} is right." if res["passed"] else f"{name} is not what I expected.{_none_hint(act, exp)}"
        )
        return res

    if ctype == "function":
        name = check["name"]
        learner_calls = learner["calls"].get(cid, [])
        ref_calls = reference["calls"].get(cid, [])
        if any(kind == "missing" for kind, _ in learner_calls) or not learner_calls:
            fn = learner["ns"].get(name, MISSING)
            res["actual"] = "(not defined)" if fn is MISSING else f"{show(fn)} is not a function"
            res["message"] = f"I couldn't find a function called {name} – check the name after def."
            return res
        for call, (lkind, lval), (rkind, rval) in zip(check["calls"], learner_calls, ref_calls, strict=True):
            text = _call_text(name, call, params)
            if rkind != "ok":
                res["message"] = "The reference solution failed – this task has a bug. Please tell the organiser."
                return res
            res["expected"] = f"{text} → {show(rval)}"
            if lkind == "error":
                res["actual"] = f"{text} → {lval['last_line']}"
                res["message"] = f"Calling {text} raised an error. {lval['friendly']}"
                res["error_line"] = lval["line"]
                return res
            res["actual"] = f"{text} → {show(lval)}"
            if not values_equal(lval, rval, abs_tol, rel_tol):
                hint = ""
                if lval is None and rval is not None:
                    hint = " Your function gave back None – did it print the answer instead of using return?"
                res["message"] = f"{text} gave a different answer.{hint}"
                return res
        res["passed"] = True
        res["message"] = f"{name} gives the right answer for all {len(learner_calls)} test call(s)."
        return res

    res["message"] = f"Unknown check type {ctype!r} – this task has a bug."
    return res


# ── public entry points ──────────────────────────────────────────────────────


def run_task(
    code: str,
    reference_src: str,
    params: dict,
    inject_params: bool,
    checks: list,
    seed: int,
    allow_plot: bool,
) -> dict:
    reference_code = substitute_code(reference_src, params)
    reference = evaluate(reference_code, params, inject_params, checks, seed, allow_plot)
    learner = evaluate(code, params, inject_params, checks, seed, allow_plot)
    results = [compare(check, learner, reference, params) for check in checks]
    notes = []
    lines = caret_lines(code)
    if lines:
        notes.append(
            f"Line {lines[0]} uses ^. In Python ^ is not 'to the power of' (3 ^ 2 is 1); use ** instead."
        )
    return {
        "learner": {
            "stdout": learner["stdout"],
            "stderr": learner["stderr"],
            "error": learner["error"],
            "plots": learner["plots"],
            "notes": notes,
        },
        "checks": results,
        "passed": bool(results) and all(r["passed"] for r in results),
    }


def run_task_json(request_json: str) -> str:
    req = json.loads(request_json)
    out = run_task(
        code=req["code"],
        reference_src=req.get("referenceSrc", ""),
        params=req.get("params") or {},
        inject_params=bool(req.get("injectParams")),
        checks=req.get("checks") or [],
        seed=int(req.get("seed", 0)),
        allow_plot=bool(req.get("allowPlot")),
    )
    return json.dumps(out)
