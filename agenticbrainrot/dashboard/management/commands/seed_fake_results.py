"""
Seed fake completed sessions for a participant to preview the results dashboard.
Usage: python manage.py seed_fake_results --email user@example.com
"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from agenticbrainrot.accounts.models import Participant
from agenticbrainrot.accounts.models import User
from agenticbrainrot.challenges.models import Challenge
from agenticbrainrot.challenges.models import ChallengeAttempt
from agenticbrainrot.coding_sessions.models import CodeSession
from agenticbrainrot.coding_sessions.models import CodeSessionChallenge


class Command(BaseCommand):
    help = "Seed fake completed sessions for dashboard preview"

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="User email")
        parser.add_argument("--sessions", type=int, default=7, help="Number of sessions to create")
        parser.add_argument("--challenges-per-session", type=int, default=8, help="Challenges per session")
        parser.add_argument("--clear", action="store_true", help="Delete existing fake sessions first")

    def handle(self, *args, **options):
        user = User.objects.get(email=options["email"])
        participant = Participant.objects.get(user=user)
        n_sessions = options["sessions"]
        n_challenges = options["challenges_per_session"]

        if options["clear"]:
            deleted, _ = CodeSession.objects.filter(participant=participant, is_mock=True).delete()
            self.stdout.write(f"Cleared {deleted} existing mock sessions.")

        all_challenges = list(Challenge.objects.filter(is_active=True))
        if len(all_challenges) < n_challenges:
            self.stderr.write("Not enough active challenges.")
            return

        # Sessions spread ~28 days apart going back from today
        # Speed degrades: base ~120s rising to ~260s by last session
        # Accuracy degrades: base ~88% dropping to ~62% by last session
        now = timezone.now()

        # Build session dates working backwards from today, each gap >= 28 days
        gaps = [28 + random.randint(0, 14) for _ in range(n_sessions)]
        cumulative = [sum(gaps[i:]) for i in range(n_sessions)]

        for i in range(n_sessions):
            # Oldest session first
            days_ago = cumulative[i]
            started = now - timedelta(days=days_ago, hours=random.randint(9, 20))
            completed = started + timedelta(minutes=random.randint(25, 55))

            # Degradation factor 0.0 (first session) → 1.0 (last session)
            t = i / max(n_sessions - 1, 1)

            session = CodeSession.objects.create(
                participant=participant,
                status=CodeSession.Status.COMPLETED,
                started_at=started,
                completed_at=completed,
                challenges_attempted=n_challenges,
                device_type=CodeSession.DeviceType.LAPTOP,
                distraction_free=CodeSession.DistractionFree.MOSTLY,
                is_mock=True,
            )
            # Override auto_now_add
            CodeSession.objects.filter(pk=session.pk).update(started_at=started)

            challenges = random.sample(all_challenges, n_challenges)

            for pos, challenge in enumerate(challenges):
                CodeSessionChallenge.objects.create(
                    session=session,
                    challenge=challenge,
                    position=pos,
                )

                # Time taken: starts ~120s, drifts up to ~260s with noise
                base_time = 120 + t * 140
                time_taken = max(30, base_time + random.gauss(0, 25))
                active_time = time_taken * random.uniform(0.55, 0.80)
                idle_time = time_taken - active_time

                # Accuracy: starts ~88%, drops to ~62%
                base_accuracy = 0.88 - t * 0.26
                pass_rate = min(1.0, max(0.0, base_accuracy + random.gauss(0, 0.12)))
                tests_total = random.choice([3, 4, 5])
                tests_passed = round(pass_rate * tests_total)

                attempt_time = started + timedelta(minutes=pos * 5 + random.randint(1, 4))

                # Runs before submitting: starts ~2, drifts up to ~5 as confidence drops
                base_runs = 2 + t * 3
                run_count = max(1, round(base_runs + random.gauss(0, 0.8)))

                attempt = ChallengeAttempt(
                    participant=participant,
                    challenge=challenge,
                    session=session,
                    submitted_code="# fake\npass",
                    tests_passed=tests_passed,
                    tests_total=tests_total,
                    time_taken_seconds=round(time_taken, 1),
                    active_time_seconds=round(active_time, 1),
                    idle_time_seconds=round(idle_time, 1),
                    submitted_at=attempt_time,
                    skipped=False,
                    keystroke_count=random.randint(40, 300),
                    paste_count=0,
                    paste_total_chars=0,
                    tab_blur_count=random.randint(0, 4),
                    run_count=run_count,
                )
                # bypass auto_now_add on started_at
                attempt.save()
                ChallengeAttempt.objects.filter(pk=attempt.pk).update(started_at=attempt_time)

            self.stdout.write(
                f"  Session {i + 1}: {completed.strftime('%d %b %Y')}  "
                f"avg_time≈{base_time:.0f}s  pass_rate≈{base_accuracy:.0%}"
            )

        self.stdout.write(self.style.SUCCESS(f"Done. Created {n_sessions} sessions for {user.email}."))
