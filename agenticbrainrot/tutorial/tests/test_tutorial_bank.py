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
    rep = _builder().build(sample=True, check=True, quiet=True)
    assert rep.errors == []
