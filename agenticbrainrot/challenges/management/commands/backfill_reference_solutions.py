"""
Backfill reference_solution in fixture files and DB from MBPP and HumanEval source datasets.

Downloads the source JSONL files, matches fixtures by dataset_id, writes
reference_solution into each fixture JSON file, and updates the corresponding
Challenge DB record in the same pass.

Usage:
    python manage.py backfill_reference_solutions
    python manage.py backfill_reference_solutions --dry-run
    python manage.py backfill_reference_solutions --overwrite   # re-fetch even if already set
"""

import gzip
import json
import urllib.request
from pathlib import Path

from django.core.management.base import BaseCommand

from agenticbrainrot.challenges.models import Challenge

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"

MBPP_URL = (
    "https://raw.githubusercontent.com/google-research/google-research"
    "/master/mbpp/mbpp.jsonl"
)
HUMANEVAL_URL = (
    "https://github.com/openai/human-eval/raw/master/data/HumanEval.jsonl.gz"
)

TIMEOUT = 30  # seconds


def _fetch_mbpp():
    """Returns {task_id (int): canonical solution code}."""
    with urllib.request.urlopen(MBPP_URL, timeout=TIMEOUT) as resp:
        raw = resp.read().decode("utf-8")
    result = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        # Normalise Windows line endings that appear in some MBPP entries
        code = entry["code"].replace("\r\n", "\n").replace("\r", "\n")
        result[entry["task_id"]] = code
    return result


def _fetch_humaneval():
    """Returns {task_id (int): full executable function string}."""
    with urllib.request.urlopen(HUMANEVAL_URL, timeout=TIMEOUT) as resp:
        raw = gzip.decompress(resp.read()).decode("utf-8")
    result = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        # task_id is "HumanEval/53" -> 53
        num = int(entry["task_id"].split("/")[1])
        # canonical_solution is the function body only; prompt contains the def + docstring
        result[num] = entry["prompt"] + entry["canonical_solution"]
    return result


class Command(BaseCommand):
    help = "Backfill reference_solution from MBPP and HumanEval source datasets."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change without writing anything.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Replace existing reference_solution values.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        overwrite = options["overwrite"]

        self.stdout.write("Fetching MBPP dataset...")
        try:
            mbpp = _fetch_mbpp()
            self.stdout.write(f"  {len(mbpp)} entries.")
        except Exception as exc:
            self.stderr.write(f"Failed to fetch MBPP: {exc}")
            mbpp = {}

        self.stdout.write("Fetching HumanEval dataset...")
        try:
            humaneval = _fetch_humaneval()
            self.stdout.write(f"  {len(humaneval)} entries.")
        except Exception as exc:
            self.stderr.write(f"Failed to fetch HumanEval: {exc}")
            humaneval = {}

        updated_files = 0
        updated_db = 0
        skipped = 0
        not_found = 0

        for json_file in sorted(FIXTURES_DIR.glob("d[1-5]/**/*.json")):
            data = json.loads(json_file.read_text(encoding="utf-8"))

            if data.get("reference_solution") and not overwrite:
                skipped += 1
                continue

            src = data.get("source", {})
            dataset_id = src.get("dataset_id", "")
            dataset = src.get("dataset", "").lower()

            reference_solution = None

            if "mbpp" in dataset and dataset_id.startswith("mbpp-"):
                task_id = int(dataset_id.split("-")[1])
                reference_solution = mbpp.get(task_id)

            elif "humaneval" in dataset and dataset_id.startswith("humaneval-"):
                task_id = int(dataset_id.split("-")[1])
                reference_solution = humaneval.get(task_id)

            if not reference_solution:
                not_found += 1
                self.stderr.write(f"  No solution for {json_file.name} ({dataset_id})")
                continue

            if dry_run:
                self.stdout.write(f"  [dry-run] {json_file.name} ({dataset_id})")
                updated_files += 1
                continue

            # Write fixture file
            data["reference_solution"] = reference_solution
            json_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            updated_files += 1

            # Update DB record
            n = Challenge.objects.filter(external_id=data["external_id"]).update(
                reference_solution=reference_solution
            )
            if n:
                updated_db += 1

        verb = "[dry-run] would update" if dry_run else "updated"
        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Fixture files {verb}: {updated_files} | "
            f"DB records updated: {updated_db} | "
            f"Already set (skipped): {skipped} | "
            f"Not found in source: {not_found}"
        ))
