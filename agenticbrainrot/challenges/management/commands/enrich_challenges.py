"""
Populate Challenge.clarification via the Anthropic API.

For each challenge that lacks a clarification (or --force), send the
description, skeleton code, and test cases to Claude and store the
returned plain-text explanation in Challenge.clarification.

Usage:
    python manage.py enrich_challenges
    python manage.py enrich_challenges --tier 1
    python manage.py enrich_challenges --force
    python manage.py enrich_challenges --dry-run
"""

import json
import logging

import anthropic
from django.core.management.base import BaseCommand

from agenticbrainrot.challenges.models import Challenge

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are helping participants in a coding study understand what a Python function is expected to do.
Write a short, plain-text clarification for the challenge below.

Structure your response EXACTLY as follows (no markdown headers, no bullet symbols, just labelled sections):

Parameters:
One sentence per parameter explaining its name, type, and valid range or examples.

Examples:
Two worked examples showing a realistic function call and its return value, with a one-line explanation of why.

Keep the whole response under 120 words. Use plain text only – no markdown, no code blocks.\
"""


def _build_user_message(challenge: Challenge) -> str:
    cases = challenge.test_cases[:2]
    cases_text = json.dumps(cases, indent=2)
    return (
        f"Title: {challenge.title}\n\n"
        f"Description: {challenge.description}\n\n"
        f"Skeleton code:\n{challenge.skeleton_code}\n\n"
        f"Sample test cases:\n{cases_text}"
    )


def _generate_clarification(client: anthropic.Anthropic, challenge: Challenge) -> str:
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_message(challenge)}],
    )
    return message.content[0].text.strip()


class Command(BaseCommand):
    help = "Populate Challenge.clarification via the Anthropic API."

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
            help="Regenerate clarification even if one already exists.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be generated without saving.",
        )

    def handle(self, *args, **options):
        client = anthropic.Anthropic()

        qs = Challenge.objects.filter(is_active=True)
        if options["tier"]:
            qs = qs.filter(difficulty=options["tier"])
        if not options["force"]:
            qs = qs.filter(clarification="")

        total = qs.count()
        if total == 0:
            self.stdout.write("No challenges to enrich.")
            return

        self.stdout.write(f"Enriching {total} challenge(s)...")
        done = 0
        errors = 0

        for challenge in qs.iterator():
            try:
                clarification = _generate_clarification(client, challenge)
            except anthropic.APIError as exc:
                errors += 1
                logger.error("API error for %s: %s", challenge.external_id, exc)
                self.stderr.write(f"  ERROR {challenge.external_id}: {exc}")
                continue

            if options["dry_run"]:
                self.stdout.write(f"\n--- {challenge.title} ---\n{clarification}\n")
            else:
                challenge.clarification = clarification
                challenge.save(update_fields=["clarification", "updated_at"])
                done += 1
                self.stdout.write(f"  {done}/{total} {challenge.title}")

        verb = "Would enrich" if options["dry_run"] else "Enriched"
        self.stdout.write(self.style.SUCCESS(
            f"\n{verb}: {done}, Errors: {errors}"
        ))
