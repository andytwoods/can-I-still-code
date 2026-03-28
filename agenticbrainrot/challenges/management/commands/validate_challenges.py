"""
Validate challenge JSON fixture files.

Checks each file in challenges/fixtures/d1-d5/ for:
- Required fields present
- Correct difficulty range (1-5) matching directory
- Valid test_cases structure
- No duplicate external_ids
- external_id matches filename
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"

REQUIRED_FIELDS = {
    "external_id",
    "title",
    "description",
    "skeleton_code",
    "test_cases",
    "difficulty",
}


def _validate_test_case(tc, file_path):
    """Validate a single test case dict. Returns list of error strings."""
    errors = []
    if not isinstance(tc, dict):
        errors.append(f"{file_path}: test_case is not a dict")
        return errors

    if "description" not in tc:
        errors.append(f"{file_path}: test_case missing 'description'")

    inp = tc.get("input")
    if inp == "operations":
        if "ops" not in tc:
            errors.append(f"{file_path}: operations test missing 'ops'")
        if "expected" not in tc:
            errors.append(f"{file_path}: operations test missing 'expected'")
    elif inp == "tree_ops":
        if "tree" not in tc:
            errors.append(f"{file_path}: tree_ops test missing 'tree'")
    else:
        has_expected = any(k in tc for k in ("expected", "expected_in", "expected_sorted"))
        if not has_expected:
            errors.append(f"{file_path}: test_case missing expected value")
    return errors


def _validate_file(json_file, expected_difficulty, seen_ids):
    """Validate a single fixture file. Returns (errors, n_tests)."""
    errors = []
    rel = f"{json_file.parent.name}/{json_file.name}"

    try:
        data = json.loads(json_file.read_text())
    except json.JSONDecodeError as exc:
        return [f"{rel}: invalid JSON: {exc}"], 0

    if not isinstance(data, dict):
        return [f"{rel}: root is not a dict"], 0

    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        return [f"{rel}: missing fields: {missing}"], 0

    ext_id = data["external_id"]

    if json_file.name != f"{ext_id}.json":
        errors.append(
            f"{rel}: filename doesn't match external_id '{ext_id}'",
        )

    if ext_id in seen_ids:
        errors.append(
            f"{rel}: duplicate external_id '{ext_id}' (also in {seen_ids[ext_id]})",
        )
    seen_ids[ext_id] = rel

    if data["difficulty"] != expected_difficulty:
        errors.append(
            f"{rel}: difficulty {data['difficulty']} doesn't match directory d{expected_difficulty}",
        )

    n_tests = 0
    tcs = data["test_cases"]
    if not isinstance(tcs, list) or len(tcs) == 0:
        errors.append(f"{rel}: test_cases must be a non-empty list")
    else:
        n_tests = len(tcs)
        for tc in tcs:
            errors.extend(_validate_test_case(tc, rel))

    if not data["skeleton_code"].strip():
        errors.append(f"{rel}: skeleton_code is empty")

    return errors, n_tests


class Command(BaseCommand):
    help = "Validate challenge fixture JSON files."

    def handle(self, *args, **options):
        all_errors = []
        seen_ids = {}
        total_files = 0
        total_tests = 0

        for tier_dir in sorted(FIXTURES_DIR.glob("d[1-5]")):
            if not tier_dir.is_dir():
                continue

            expected_difficulty = int(tier_dir.name[1])

            for json_file in sorted(tier_dir.glob("*.json")):
                total_files += 1
                errors, n_tests = _validate_file(
                    json_file,
                    expected_difficulty,
                    seen_ids,
                )
                all_errors.extend(errors)
                total_tests += n_tests

        if all_errors:
            for err in all_errors:
                self.stderr.write(self.style.ERROR(err))
            self.stderr.write(
                f"\n{len(all_errors)} error(s) in {total_files} files.",
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"All {total_files} fixture files valid ({total_tests} test cases).",
                ),
            )
