"""
Flag ChallengeAttempt records whose accuracy data is unreliable due to a known
fixture or runner bug, so analysts can exclude them.

Usage:
    uv run manage.py flag_affected_attempts               # dry-run
    uv run manage.py flag_affected_attempts --apply       # write flags to DB
"""

import logging
from datetime import datetime
from datetime import timezone

from django.core.management.base import BaseCommand

from agenticbrainrot.challenges.models import Challenge
from agenticbrainrot.challenges.models import ChallengeAttempt

logger = logging.getLogger(__name__)

# Each entry: (deviation_id, external_id, cutoff_dt)
# cutoff_dt is the moment the fix was deployed; attempts before this are flagged.
_CUTOFF = datetime(2026, 5, 25, 0, 0, 0, tzinfo=timezone.utc)
KNOWN_ISSUES = [
    ("DEV-001", "special-factorial-v1",      _CUTOFF),
    ("DEV-001", "vowels-count-v1",           _CUTOFF),
    ("DEV-001", "closest-integer-v1",        _CUTOFF),
    ("DEV-001", "double-the-difference-v1",  _CUTOFF),
    ("DEV-001", "right-angle-triangle-v1",   _CUTOFF),
    ("DEV-001", "triangle-area-d5-v1",       _CUTOFF),
]


class Command(BaseCommand):
    help = "Flag ChallengeAttempt records affected by known fixture/runner bugs (see fixtures/DEVIATIONS.md)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="Write flags to the database. Without this flag the command runs as a dry-run.",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        total_flagged = 0

        for deviation_id, external_id, cutoff_dt in KNOWN_ISSUES:
            try:
                challenge = Challenge.objects.get(external_id=external_id)
            except Challenge.DoesNotExist:
                self.stderr.write(f"Challenge {external_id!r} not found – skipped.")
                continue

            qs = ChallengeAttempt.objects.filter(
                challenge=challenge,
                started_at__lt=cutoff_dt,
                data_quality_flag="",
            )
            count = qs.count()

            self.stdout.write(
                f"{deviation_id}: {count} attempt(s) on {external_id!r} before {cutoff_dt.date()}"
                + (" [DRY RUN]" if not apply else ""),
            )

            if apply and count:
                updated = qs.update(data_quality_flag=deviation_id)
                self.stdout.write(self.style.SUCCESS(f"  Flagged {updated} attempt(s)."))
                total_flagged += updated
            elif not apply and count:
                self.stdout.write("  Run with --apply to write flags.")

        if apply:
            self.stdout.write(self.style.SUCCESS(f"Done. Total flagged: {total_flagged}"))
        else:
            self.stdout.write("Dry-run complete. No changes made.")
