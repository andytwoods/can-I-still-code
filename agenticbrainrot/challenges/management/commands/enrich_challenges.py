"""
Populate Challenge.clarification from the pre-generated clarifications fixture.

Reads agenticbrainrot/challenges/fixtures/clarifications.json and saves each
clarification to the matching Challenge row (looked up by external_id).

Usage:
    python manage.py enrich_challenges
    python manage.py enrich_challenges --tier 1
    python manage.py enrich_challenges --force
    python manage.py enrich_challenges --dry-run
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from agenticbrainrot.challenges.models import Challenge

CLARIFICATIONS_FILE = Path(__file__).resolve().parent.parent.parent / "fixtures" / "clarifications.json"


class Command(BaseCommand):
    help = "Populate Challenge.clarification from fixtures/clarifications.json."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tier",
            type=int,
            choices=[1, 2, 3, 4, 5],
            default=None,
            help="Only process a specific difficulty tier.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite clarification even if one already exists.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be saved without writing to the database.",
        )

    def handle(self, *args, **options):
        clarifications = json.loads(CLARIFICATIONS_FILE.read_text())

        qs = Challenge.objects.filter(is_active=True)
        if options["tier"]:
            qs = qs.filter(difficulty=options["tier"])
        if not options["force"]:
            qs = qs.filter(clarification="")

        done = 0
        skipped = 0

        for challenge in qs.iterator():
            text = clarifications.get(challenge.external_id)
            if not text:
                skipped += 1
                continue

            if options["dry_run"]:
                self.stdout.write(f"\n--- {challenge.title} ---\n{text}\n")
            else:
                challenge.clarification = text
                challenge.save(update_fields=["clarification", "updated_at"])
                done += 1
                self.stdout.write(f"  {challenge.external_id}")

        verb = "Would update" if options["dry_run"] else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{verb}: {done}, No clarification found: {skipped}",
            )
        )
