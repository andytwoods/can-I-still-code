"""
Seed challenges from JSON fixture files.

Reads individual challenge JSON files from challenges/fixtures/d0/ through d5/.
Idempotent: skips challenges whose external_id already exists.
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from agenticbrainrot.challenges.models import Challenge

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"


class Command(BaseCommand):
    help = "Seed coding challenges from fixture JSON files (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tier",
            type=int,
            choices=[0, 1, 2, 3, 4, 5],
            default=None,
            help="Only seed a specific tier (d0-d5).",
        )

    def handle(self, *args, **options):
        tier = options["tier"]
        created = 0
        skipped = 0
        updated = 0
        errors = 0

        dirs = [FIXTURES_DIR / f"d{tier}"] if tier is not None else sorted(FIXTURES_DIR.glob("d[0-5]"))

        for tier_dir in dirs:
            if not tier_dir.is_dir():
                self.stderr.write(f"Directory not found: {tier_dir}")
                continue

            for json_file in sorted(tier_dir.glob("*.json")):
                try:
                    data = json.loads(json_file.read_text())
                    challenge, was_created = Challenge.objects.get_or_create(
                        external_id=data["external_id"],
                        defaults={
                            "title": data["title"],
                            "description": data["description"],
                            "skeleton_code": data["skeleton_code"],
                            "test_cases": data["test_cases"],
                            "difficulty": data["difficulty"],
                            "tags": data.get("tags", []),
                            "source": data.get("source", {}),
                            "source_metadata": data.get("metadata", {}),
                            "reference_solution": data.get("reference_solution", ""),
                            "clarification": data.get("clarification", ""),
                            "is_active": data.get("is_active", True),
                        },
                    )
                    # Always sync clarification and reference_solution so they can be updated post-creation
                    if not was_created:
                        update_fields = []
                        new_clarification = data.get("clarification", "")
                        if challenge.clarification != new_clarification:
                            challenge.clarification = new_clarification
                            update_fields.append("clarification")
                        new_ref = data.get("reference_solution", "")
                        if challenge.reference_solution != new_ref:
                            challenge.reference_solution = new_ref
                            update_fields.append("reference_solution")
                        if update_fields:
                            challenge.save(update_fields=update_fields)
                            updated += 1
                    if was_created:
                        created += 1
                    else:
                        skipped += 1  # exists; may have been updated above
                except Exception as exc:  # noqa: BLE001
                    errors += 1
                    self.stderr.write(
                        f"Error loading {json_file.name}: {exc}",
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created: {created}, Updated: {updated}, Skipped (no change): {skipped - updated}, Errors: {errors}",
            ),
        )
