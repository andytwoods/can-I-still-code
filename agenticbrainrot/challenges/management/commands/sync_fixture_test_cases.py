"""
Sync test_cases from fixture JSON files into the Challenge DB records.

seed_challenges uses get_or_create so it never updates test_cases for existing
rows. This command does the targeted update and is safe to re-run (idempotent).

Usage:
    uv run manage.py sync_fixture_test_cases                          # dry-run
    uv run manage.py sync_fixture_test_cases --apply                  # write to DB
    uv run manage.py sync_fixture_test_cases --apply --settings=...   # remote DB
"""

import json
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

from agenticbrainrot.challenges.models import Challenge

logger = logging.getLogger(__name__)

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "challenges" / "fixtures"


class Command(BaseCommand):
    help = "Sync test_cases from fixture JSON files into Challenge DB rows (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="Write changes to the database. Without this flag the command is a dry-run.",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        updated = 0
        skipped = 0
        missing = 0

        for json_path in sorted(FIXTURES_DIR.glob("d[0-9]/*.json")):
            data = json.loads(json_path.read_text())
            external_id = data.get("external_id")
            fixture_cases = data.get("test_cases", [])

            try:
                challenge = Challenge.objects.get(external_id=external_id)
            except Challenge.DoesNotExist:
                self.stderr.write(f"  MISSING in DB: {external_id}")
                missing += 1
                continue

            if challenge.test_cases == fixture_cases:
                skipped += 1
                continue

            self.stdout.write(f"  {'UPDATE' if apply else 'WOULD UPDATE'}: {external_id}")

            if apply:
                Challenge.objects.filter(pk=challenge.pk).update(test_cases=fixture_cases)
                updated += 1

        if apply:
            self.stdout.write(self.style.SUCCESS(f"Done. Updated: {updated}, unchanged: {skipped}, missing: {missing}"))
        else:
            self.stdout.write(f"Dry-run complete. Would update: {updated}, unchanged: {skipped}, missing: {missing}")
            self.stdout.write("Run with --apply to write changes.")
