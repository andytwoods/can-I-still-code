"""Runs the bank builder: every template, 30 seeds, through the browser's runner."""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _builder():
    spec = importlib.util.spec_from_file_location("build_tutorial_bank", ROOT / "scripts" / "build_tutorial_bank.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses look the module up
    spec.loader.exec_module(module)
    return module


def test_bank_is_valid_and_bundle_is_up_to_date():
    rep = _builder().build(check=True, quiet=True)
    assert rep.errors == []


def test_fallback_notebook_is_up_to_date():
    import json  # noqa: PLC0415

    spec = importlib.util.spec_from_file_location(
        "export_tutorial_colab", ROOT / "scripts" / "export_tutorial_colab.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    expected = json.dumps(module.build_notebook(), indent=1, ensure_ascii=False) + "\n"
    assert module.OUT.read_text(encoding="utf-8") == expected, "run scripts/export_tutorial_colab.py"
