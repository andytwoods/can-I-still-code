"""Validate the tutorial task bank and write the browser bundle.

Sources: docs/tutorial/bank/block*.json (one file per block, edited by authors).
Output:  agenticbrainrot/static/tutorial/bank.bundle.json (generated; never edit).

    uv run python scripts/build_tutorial_bank.py            # full mode, write the bundle
    uv run python scripts/build_tutorial_bank.py --sample   # skip completeness checks
    uv run python scripts/build_tutorial_bank.py --check    # validate; fail if the bundle is stale
    uv run python scripts/build_tutorial_bank.py --block 3  # validate one block only; writes nothing

Every template is run for 30 seeds with the same runner the browser uses
(agenticbrainrot/static/tutorial/tutorial_runner.py). See docs/tutorial/README.md.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import signal
import sys
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
BANK_DIR = ROOT / "docs" / "tutorial" / "bank"
README = ROOT / "docs" / "tutorial" / "README.md"
STATIC_DIR = ROOT / "agenticbrainrot" / "static" / "tutorial"
BUNDLE = STATIC_DIR / "bank.bundle.json"

sys.dont_write_bytecode = True  # keep __pycache__ out of the static directory
sys.path.insert(0, str(STATIC_DIR))
import tutorial_runner as runner  # noqa: E402

SCHEMA_VERSION = 1
SEEDS = range(1, 31)
MIN_DISTINCT_PARAMS = 10
BLOCKS = (1, 2, 3, 4, 5)
LEVELS = (1, 2, 3, 4, 5)
KINDS = ("check", "core", "practice", "fix")
ALLOWED_IMPORTS = {"random", "math", "matplotlib", "matplotlib.pyplot"}
CHECK_TYPES = {"variable", "function", "stdout", "no_error"}
REQUIRED = {
    "schema_version": int,
    "id": str,
    "block": int,
    "kind": str,
    "title": str,
    "prompt_md": str,
    "starter_code": str,
    "reference": str,
    "checks": list,
    "hints": list,
}
OPTIONAL = {
    "level": (int, type(None)),
    "inject_params": bool,
    "fixed_seed": (int, type(None)),
    "generator": (str, type(None)),
    "wrong_examples": list,
    "alternative_solutions": list,
    "allow_plot": bool,
    "solution_md": (str, type(None)),
}
BLOCK5_LADDER_CUT_MARKER = "BLOCK 5 LADDER CUT"
RUN_TIME_LIMIT_S = 5


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, where: str, msg: str):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str):
        self.warnings.append(f"{where}: {msg}")


# ── markdown ────────────────────────────────────────────────────────────────


def render_md(text: str) -> str:
    """Markdown to HTML with raw HTML disabled (it is escaped as text).

    ``@@param@@`` tokens survive as plain text; the browser fills them in.
    """
    md = markdown.Markdown(extensions=["fenced_code", "sane_lists"])
    md.preprocessors.deregister("html_block")
    md.inlinePatterns.deregister("html")
    md.inlinePatterns.deregister("entity")
    return md.convert(text or "")


# ── time limit ──────────────────────────────────────────────────────────────


class _Timeout(KeyboardInterrupt):  # the runner re-raises KeyboardInterrupt
    pass


def _alarm(_signum, _frame):
    raise _Timeout


def timed(fn, *args):
    if not hasattr(signal, "setitimer"):
        return fn(*args)
    old = signal.signal(signal.SIGALRM, _alarm)
    signal.setitimer(signal.ITIMER_REAL, RUN_TIME_LIMIT_S)
    try:
        return fn(*args)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


# ── per-template checks ─────────────────────────────────────────────────────


def _imports(src: str) -> set[str]:
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return set()  # broken starter code is allowed ("fix" tasks); only exec matters
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
    return names


def check_schema(t: dict, where: str, rep: Report) -> bool:
    ok = True
    for key, typ in REQUIRED.items():
        if key not in t:
            rep.error(where, f"missing field {key!r}")
            ok = False
        elif not isinstance(t[key], typ):
            rep.error(where, f"{key!r} should be {typ.__name__}")
            ok = False
    for key, typ in OPTIONAL.items():
        if key in t and not isinstance(t[key], typ):
            rep.error(where, f"{key!r} has the wrong type")
            ok = False
    unknown = set(t) - set(REQUIRED) - set(OPTIONAL)
    if unknown:
        rep.error(where, f"unknown field(s) {sorted(unknown)}")
        ok = False
    if not ok:
        return False
    if t["schema_version"] != SCHEMA_VERSION:
        rep.error(where, f"schema_version must be {SCHEMA_VERSION}")
    if t["kind"] not in KINDS:
        rep.error(where, f"kind must be one of {KINDS}")
    if t["kind"] in ("practice", "fix"):
        if t.get("level") not in LEVELS:
            rep.error(where, "practice/fix tasks need a level 1-5")
    elif t.get("level") is not None:
        rep.error(where, "only practice/fix tasks have a level")
    if t["kind"] == "core" and not isinstance(t.get("fixed_seed"), int):
        rep.error(where, "core tasks need an integer fixed_seed (the room sees the same numbers)")
    if t["kind"] == "fix" and t["block"] != 3:  # noqa: PLR2004
        rep.error(where, "fix tasks belong to Block 3")
    if t.get("allow_plot") and t["kind"] != "core":
        rep.error(where, "only core tasks may set allow_plot")
    if not t["checks"]:
        rep.error(where, "at least one check is required")
    if not t["hints"]:
        rep.error(where, "at least one hint is required")
    ids = set()
    for c in t["checks"]:
        if not isinstance(c, dict) or c.get("type") not in CHECK_TYPES or not c.get("id"):
            rep.error(where, f"bad check {c!r}")
            continue
        if c["id"] in ids:
            rep.error(where, f"duplicate check id {c['id']!r}")
        ids.add(c["id"])
        if c["type"] in ("variable", "function") and not c.get("name"):
            rep.error(where, f"check {c['id']!r} needs a name")
        if c["type"] == "function" and not c.get("calls"):
            rep.error(where, f"check {c['id']!r} needs calls")
        if c["type"] == "stdout" and c.get("normalise", "strip") not in ("exact", "strip"):
            rep.error(where, f"check {c['id']!r}: normalise must be exact or strip")
    for name, src in _code_fields(t):
        bad = _imports(src) - ALLOWED_IMPORTS
        if bad:
            rep.error(where, f"{name} imports {sorted(bad)}; only {sorted(ALLOWED_IMPORTS)} are allowed")
    if "{" in t.get("prompt_md", "") and "@@" not in t["prompt_md"] and "{}" in t["prompt_md"]:
        rep.warn(where, "prompt has {} – placeholders are @@name@@, not str.format")
    return not rep.errors


def _code_fields(t: dict):
    yield "generator", t.get("generator") or ""
    yield "reference", t["reference"]
    yield "starter_code", t["starter_code"]
    for i, src in enumerate(t.get("wrong_examples", [])):
        yield f"wrong_examples[{i}]", src
    for i, src in enumerate(t.get("alternative_solutions", [])):
        yield f"alternative_solutions[{i}]", src


def _uses_random(t: dict) -> bool:
    return "random" in _imports(t["reference"])


def _run(t: dict, code: str, params: dict, seed: int) -> dict:
    return timed(
        runner.run_task,
        code,
        t["reference"],
        params,
        bool(t.get("inject_params")),
        t["checks"],
        seed,
        bool(t.get("allow_plot")),
    )


def _failing(result: dict) -> str:
    bad = [c for c in result["checks"] if not c["passed"]]
    if not bad:
        return ""
    c = bad[0]
    err = result["learner"]["error"]
    extra = f" [error: {err['last_line']}]" if err else ""
    return f"check {c['id']!r}: {c['message']} expected={c['expected']!r} actual={c['actual']!r}{extra}"


def validate_template(t: dict, rep: Report):
    where = t["id"]
    if _uses_random(t) and not t.get("alternative_solutions"):
        rep.error(where, "randomness templates need at least one alternative_solutions entry")
    if t["kind"] != "core" and not t.get("generator"):
        rep.error(where, "needs a generator (New example must give a fresh variant)")
    seen = set()
    seeds = list(SEEDS)
    if isinstance(t.get("fixed_seed"), int) and t["fixed_seed"] not in seeds:
        seeds.append(t["fixed_seed"])
    for seed in seeds:
        tag = f"{where} seed {seed}"
        try:
            params = timed(runner.generate, t.get("generator"), seed)
        except (Exception, _Timeout) as exc:  # noqa: BLE001 - report every generator failure
            rep.error(tag, f"generator failed: {type(exc).__name__}: {exc}")
            return
        seen.add(json.dumps(params, sort_keys=True))
        try:
            for field_name, src in _code_fields(t):
                if field_name != "generator":
                    runner.substitute_code(src, params)
            runner.substitute_args([c.get("calls", []) for c in t["checks"]], params)
        except runner.PlaceholderError as exc:
            rep.error(tag, f"placeholder @@{exc.args[0]}@@ is not returned by the generator")
            return
        texts = [t["prompt_md"], *t["hints"], t.get("solution_md") or ""]
        for token in runner.PLACEHOLDER.findall("\n".join(texts)):
            if token not in params:
                rep.error(tag, f"placeholder @@{token}@@ in the prompt/hints is not returned by the generator")
                return
        try:
            ref = _run(t, runner.substitute_code(t["reference"], params), params, seed)
            if not ref["passed"]:
                rep.error(tag, f"reference fails its own checks: {_failing(ref)}")
            starter = _run(t, runner.substitute_code(t["starter_code"], params), params, seed)
            if starter["passed"]:
                rep.error(tag, "starter code already passes every check")
            for i, src in enumerate(t.get("wrong_examples", [])):
                if _run(t, runner.substitute_code(src, params), params, seed)["passed"]:
                    rep.error(tag, f"wrong_examples[{i}] passes but should fail")
            for i, src in enumerate(t.get("alternative_solutions", [])):
                alt = _run(t, runner.substitute_code(src, params), params, seed)
                if not alt["passed"]:
                    rep.error(tag, f"alternative_solutions[{i}] fails: {_failing(alt)}")
        except _Timeout:
            rep.error(tag, f"a run took longer than {RUN_TIME_LIMIT_S}s")
        if len(rep.errors) > 50:  # noqa: PLR2004
            return
    if t.get("generator") and len(seen) < MIN_DISTINCT_PARAMS:
        rep.error(
            where, f"only {len(seen)} distinct parameter sets across {len(SEEDS)} seeds (need {MIN_DISTINCT_PARAMS})"
        )


# ── bank level ──────────────────────────────────────────────────────────────


def load_sources(rep: Report) -> list[dict]:
    blocks = []
    for path in sorted(BANK_DIR.glob("block*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            rep.error(path.name, f"invalid JSON: {exc}")
            continue
        for key in ("schema_version", "block", "title", "explanation_md", "templates"):
            if key not in data:
                rep.error(path.name, f"missing {key!r}")
        if not rep.errors:
            for t in data["templates"]:
                if t.get("block") != data["block"]:
                    rep.error(path.name, f"{t.get('id')}: block {t.get('block')} in file for block {data['block']}")
            blocks.append(data)
    return blocks


def check_completeness(blocks: list[dict], rep: Report):
    readme = README.read_text(encoding="utf-8") if README.exists() else ""
    by_block = {b["block"]: b for b in blocks}
    for n in BLOCKS:
        b = by_block.get(n)
        if b is None:
            rep.error(f"block {n}", "missing")
            continue
        kinds = [t["kind"] for t in b["templates"]]
        if kinds.count("check") != 1:
            rep.error(f"block {n}", f"needs exactly 1 check task, has {kinds.count('check')}")
        if kinds.count("core") < 1:
            rep.error(f"block {n}", "needs core tasks")
        levels = {t.get("level") for t in b["templates"] if t["kind"] in ("practice", "fix")}
        missing = [lv for lv in LEVELS if lv not in levels]
        if missing:
            if n == 5 and BLOCK5_LADDER_CUT_MARKER in readme:  # noqa: PLR2004
                rep.warn("block 5", f"ladder levels {missing} missing (cut recorded in README)")
            else:
                rep.error(f"block {n}", f"practice ladder is missing level(s) {missing}")


def build_bundle(blocks: list[dict]) -> dict:
    out_blocks = []
    tasks = {}
    for b in sorted(blocks, key=lambda b: b["block"]):
        order = {"check": 0, "core": 1, "practice": 2, "fix": 2}
        templates = sorted(b["templates"], key=lambda t: (order[t["kind"]], t.get("level") or 0))
        out_blocks.append(
            {
                "block": b["block"],
                "title": b["title"],
                "explanation_html": render_md(b["explanation_md"]),
                "task_ids": [t["id"] for t in templates],
            }
        )
        for t in templates:
            entry = dict(t)
            entry["prompt_html"] = render_md(t["prompt_md"])
            entry["hints_html"] = [render_md(h) for h in t["hints"]]
            if t.get("solution_md"):
                entry["solution_html"] = render_md(t["solution_md"])
            for key in ("prompt_md", "hints", "solution_md", "wrong_examples", "alternative_solutions"):
                entry.pop(key, None)
            entry.setdefault("level", None)
            entry.setdefault("inject_params", False)
            entry.setdefault("fixed_seed", None)
            entry.setdefault("generator", None)
            entry.setdefault("allow_plot", False)
            tasks[t["id"]] = entry
    body = {"schema_version": SCHEMA_VERSION, "blocks": out_blocks, "tasks": tasks}
    canonical = json.dumps(body, sort_keys=True, ensure_ascii=False)
    body["bank_version"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    return body


def _warm_up_matplotlib():
    """The first import builds a font cache (~10 s); keep it out of the timed runs."""
    try:
        import matplotlib  # noqa: PLC0415

        matplotlib.use("Agg")
        import matplotlib.pyplot  # noqa: PLC0415
    except ImportError:
        pass


def build(
    *, sample: bool = False, check: bool = False, write: bool = True, quiet: bool = False, block: int | None = None
) -> Report:
    rep = Report()
    blocks = load_sources(rep)
    if block is not None:
        blocks = [b for b in blocks if b.get("block") == block]
        sample, write = True, False
    if rep.errors:
        return rep
    seen_ids = set()
    for b in blocks:
        for t in b["templates"]:
            tid = t.get("id", "?")
            if tid in seen_ids:
                rep.error(tid, "duplicate id")
            seen_ids.add(tid)
            check_schema(t, tid, rep)
    if rep.errors:
        return rep
    if not sample:
        check_completeness(blocks, rep)
    if any(t.get("allow_plot") for b in blocks for t in b["templates"]):
        _warm_up_matplotlib()
    for b in blocks:
        for t in b["templates"]:
            if not quiet:
                print(f"  validating {t['id']}", file=sys.stderr)
            validate_template(t, rep)
    if rep.errors:
        return rep
    bundle = build_bundle(blocks)
    text = json.dumps(bundle, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if check:
        current = BUNDLE.read_text(encoding="utf-8") if BUNDLE.exists() else ""
        if current != text:
            rep.error(str(BUNDLE.relative_to(ROOT)), "is stale – run scripts/build_tutorial_bank.py")
    elif write:
        BUNDLE.write_text(text, encoding="utf-8")
    return rep


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", action="store_true", help="skip completeness checks (development)")
    parser.add_argument("--check", action="store_true", help="validate only; fail if the bundle is stale")
    parser.add_argument("--block", type=int, help="validate one block only (writes nothing)")
    args = parser.parse_args(argv)
    rep = build(sample=args.sample, check=args.check, block=args.block)
    for w in rep.warnings:
        print(f"warning: {w}")
    for e in rep.errors:
        print(f"ERROR: {e}")
    if rep.errors:
        print(f"{len(rep.errors)} error(s)")
        return 1
    if args.block is not None:
        print(f"block {args.block} OK (nothing written)")
    else:
        print("bank OK" + (" (bundle up to date)" if args.check else f" – wrote {BUNDLE.relative_to(ROOT)}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
