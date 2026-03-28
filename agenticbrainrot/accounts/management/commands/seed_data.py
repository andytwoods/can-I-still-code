"""Generate realistic fake data for testing and demos."""

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
from agenticbrainrot.consent.models import ConsentDocument
from agenticbrainrot.consent.models import ConsentRecord
from agenticbrainrot.consent.models import OptionalConsentRecord
from agenticbrainrot.surveys.models import SurveyQuestion
from agenticbrainrot.surveys.models import SurveyResponse

NUM_PARTICIPANTS = 20
CHALLENGES_DATA = [
    ("two-fer", "Two Fer", 1, "def two_fer(name='you'):\n    pass"),
    ("reverse-string", "Reverse String", 1, "def reverse(text):\n    pass"),
    ("isogram", "Isogram", 2, "def is_isogram(string):\n    pass"),
    ("pangram", "Pangram", 2, "def is_pangram(sentence):\n    pass"),
    ("rna-transcription", "RNA Transcription", 2, "def to_rna(dna):\n    pass"),
    ("hamming", "Hamming", 3, "def distance(s1, s2):\n    pass"),
    ("word-count", "Word Count", 3, "def count_words(sentence):\n    pass"),
    ("matrix", "Matrix", 3, "class Matrix:\n    pass"),
    ("robot-name", "Robot Name", 4, "class Robot:\n    pass"),
    ("linked-list", "Simple Linked List", 4, "class LinkedList:\n    pass"),
    ("binary-search", "Binary Search", 4, "def find(lst, value):\n    pass"),
    ("roman-numerals", "Roman Numerals", 5, "def roman(number):\n    pass"),
]

NAMES = [
    "Alex Chen",
    "Jamie Rivera",
    "Sam Patel",
    "Morgan Lee",
    "Casey Kim",
    "Jordan Taylor",
    "Riley Johnson",
    "Avery Garcia",
    "Quinn Williams",
    "Drew Martinez",
    "Harper Brown",
    "Cameron Davis",
    "Blake Wilson",
    "Skyler Moore",
    "Finley Thomas",
    "Rowan Jackson",
    "Emery White",
    "Sage Harris",
    "Dakota Clark",
    "Reese Lewis",
]

AGES = [
    "18-24",
    "18-24",
    "18-24",
    "25-34",
    "25-34",
    "25-34",
    "25-34",
    "35-44",
    "35-44",
    "35-44",
    "35-44",
    "45-54",
    "45-54",
    "25-34",
    "18-24",
    "35-44",
    "25-34",
    "45-54",
    "25-34",
    "35-44",
]

EXPERIENCE_YEARS = [1, 2, 1, 5, 3, 8, 4, 10, 7, 6, 12, 15, 3, 2, 1, 9, 4, 20, 3, 6]

VIBE_CODING_PCTS = [
    10,
    15,
    20,
    25,
    30,
    35,
    40,
    45,
    50,
    55,
    60,
    65,
    70,
    75,
    80,
    85,
    90,
    5,
    40,
    50,
]


class Command(BaseCommand):
    help = "Generate realistic fake data for testing and demos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing seed data before creating new data.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear_data()

        challenges = self._create_challenges()
        consent_doc = self._create_consent_document()
        profile_questions = self._create_survey_questions()
        participants = self._create_participants(consent_doc)
        self._create_profile_responses(participants, profile_questions)
        self._create_sessions(participants, challenges)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed data created: {len(participants)} participants, {len(challenges)} challenges",
            ),
        )

    def _clear_data(self):
        """Remove seed users (by email pattern)."""
        User.objects.filter(email__startswith="seed").delete()
        self.stdout.write("Cleared existing seed data.")

    def _create_challenges(self):
        challenges = []
        for ext_id, title, diff, skeleton in CHALLENGES_DATA:
            challenge, _ = Challenge.objects.get_or_create(
                external_id=f"seed-{ext_id}",
                defaults={
                    "title": title,
                    "description": f"Implement the {title} exercise.",
                    "skeleton_code": skeleton,
                    "test_cases": [
                        {"input": "example", "expected": "example"},
                    ],
                    "difficulty": diff,
                    "is_active": True,
                },
            )
            challenges.append(challenge)
        return challenges

    def _create_consent_document(self):
        doc, _ = ConsentDocument.objects.get_or_create(
            version=1,
            defaults={
                "title": "Informed Consent",
                "body": "You are invited to participate in a study...",
                "is_active": True,
                "published_at": timezone.now() - timedelta(days=180),
            },
        )
        return doc

    def _create_survey_questions(self):
        questions = {}
        q_data = [
            ("age_range", "profile", "single_choice", "What is your age range?"),
            (
                "experience_years",
                "profile",
                "number",
                "Years of programming experience?",
            ),
            (
                "vibe_coding_pct",
                "post_session",
                "number",
                "Can you estimate what % of coding do you do purely with AI?",
            ),
        ]
        for cat, ctx, qtype, text in q_data:
            q, _ = SurveyQuestion.objects.get_or_create(
                category=cat,
                context=ctx,
                defaults={
                    "text": text,
                    "question_type": qtype,
                    "is_active": True,
                },
            )
            questions[cat] = q

        # Reference the canonical confidence question from seed_survey_questions
        confidence_q = SurveyQuestion.objects.filter(
            context="post_challenge",
            text="How confident are you in your solution?",
        ).first()
        if confidence_q:
            questions["confidence"] = confidence_q

        return questions

    def _create_participants(self, consent_doc):
        participants = []
        now = timezone.now()
        for i in range(NUM_PARTICIPANTS):
            email = f"seed{i + 1:02d}@example.com"
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "name": NAMES[i],
                    "is_staff": False,
                },
            )
            if created:
                user.set_password("seedpass123")
                user.save()

            participant, _ = Participant.objects.get_or_create(
                user=user,
            )
            participant.has_active_consent = True
            participant.profile_completed = True
            participant.profile_updated_at = now - timedelta(days=90)
            participant.save()

            ConsentRecord.objects.get_or_create(
                participant=participant,
                consent_document=consent_doc,
                defaults={
                    "consented": True,
                    "ip_address": f"192.168.1.{i + 10}",
                    "user_agent": "Mozilla/5.0 (seed data)",
                },
            )

            OptionalConsentRecord.objects.get_or_create(
                participant=participant,
                consent_type="reminder_emails",
                defaults={"consented": random.choice([True, False])},  # noqa: S311
            )

            participants.append(participant)

        # Participant 19: withdrawn
        p_withdrawn = participants[18]
        p_withdrawn.withdrawn_at = now - timedelta(days=10)
        p_withdrawn.has_active_consent = False
        p_withdrawn.save()

        # Participant 20: deletion requested
        p_deletion = participants[19]
        p_deletion.deletion_requested_at = now - timedelta(days=5)
        p_deletion.save()

        return participants

    def _create_profile_responses(self, participants, questions):
        for i, participant in enumerate(participants):
            if questions.get("age_range"):
                SurveyResponse.objects.get_or_create(
                    participant=participant,
                    question=questions["age_range"],
                    defaults={"value": AGES[i]},
                )
            if questions.get("experience_years"):
                SurveyResponse.objects.get_or_create(
                    participant=participant,
                    question=questions["experience_years"],
                    defaults={"value": str(EXPERIENCE_YEARS[i])},
                )

    def _create_sessions(self, participants, challenges):
        now = timezone.now()
        rng = random.Random(42)  # noqa: S311

        for i, participant in enumerate(participants):
            num_sessions = rng.randint(1, 5)
            for _s in range(num_sessions):
                days_ago = rng.randint(5, 180)
                session_start = now - timedelta(days=days_ago)

                session = CodeSession.objects.create(
                    participant=participant,
                    status=CodeSession.Status.COMPLETED,
                    completed_at=session_start + timedelta(minutes=rng.randint(20, 60)),
                    device_type=rng.choice(["desktop", "laptop"]),
                    distraction_free=rng.choice(["yes", "mostly", "no"]),
                    pyodide_load_ms=rng.randint(800, 5000),
                    editor_ready=True,
                )
                # Backdate started_at
                CodeSession.objects.filter(pk=session.pk).update(
                    started_at=session_start,
                )

                num_challenges = rng.randint(3, min(10, len(challenges)))
                selected = rng.sample(challenges, num_challenges)

                for pos, challenge in enumerate(selected):
                    CodeSessionChallenge.objects.create(
                        session=session,
                        challenge=challenge,
                        position=pos,
                    )

                    # Determine accuracy based on experience
                    exp = EXPERIENCE_YEARS[i]
                    base_accuracy = min(0.5 + exp * 0.04, 0.95)
                    # Add some noise
                    accuracy = max(0.0, min(1.0, base_accuracy + rng.gauss(0, 0.15)))

                    tests_total = rng.randint(3, 8)
                    tests_passed = round(tests_total * accuracy)
                    tests_passed = max(0, min(tests_total, tests_passed))

                    time_taken = rng.uniform(60, 600)
                    active_pct = rng.uniform(0.6, 0.95)

                    attempt = ChallengeAttempt.objects.create(
                        participant=participant,
                        challenge=challenge,
                        session=session,
                        submitted_code=f"# Solution for {challenge.title}\npass",
                        tests_passed=tests_passed,
                        tests_total=tests_total,
                        time_taken_seconds=time_taken,
                        active_time_seconds=time_taken * active_pct,
                        idle_time_seconds=time_taken * (1 - active_pct),
                        submitted_at=session_start
                        + timedelta(
                            seconds=rng.randint(120, 3000),
                        ),
                        keystroke_count=rng.randint(50, 500),
                        paste_count=rng.randint(0, 3),
                        paste_total_chars=rng.randint(0, 200),
                        tab_blur_count=rng.randint(0, 5),
                    )

                    # Post-challenge confidence response
                    confidence_q = SurveyQuestion.objects.filter(
                        category="confidence",
                        context="post_challenge",
                    ).first()
                    if confidence_q:
                        SurveyResponse.objects.create(
                            participant=participant,
                            question=confidence_q,
                            value=str(rng.randint(1, 5)),
                            challenge_attempt=attempt,
                        )

                session.challenges_attempted = num_challenges
                session.save(update_fields=["challenges_attempted"])

                # Post-session vibe coding response
                vibe_q = SurveyQuestion.objects.filter(
                    category="vibe_coding_pct",
                    context="post_session",
                ).first()
                if vibe_q:
                    base_vibe = VIBE_CODING_PCTS[i]
                    vibe_val = max(0, min(100, base_vibe + rng.randint(-10, 10)))
                    SurveyResponse.objects.create(
                        participant=participant,
                        question=vibe_q,
                        value=str(vibe_val),
                        session=session,
                    )

        self.stdout.write(
            "  Created sessions with challenge attempts and survey responses.",
        )
