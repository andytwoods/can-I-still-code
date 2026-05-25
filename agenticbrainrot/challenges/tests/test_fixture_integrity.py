"""
Tests for benchmark fixture data integrity and the flag_affected_attempts command.
"""

import json
from datetime import datetime
from datetime import timezone
from pathlib import Path

import pytest
from django.core.management import call_command
from django.utils import timezone as django_tz

from agenticbrainrot.challenges.models import Challenge
from agenticbrainrot.challenges.models import ChallengeAttempt
from agenticbrainrot.coding_sessions.models import CodeSession

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "challenges" / "fixtures"
BENCHMARK_DIRS = [FIXTURES_DIR / f"d{i}" for i in range(1, 6)]


def _all_benchmark_fixtures():
    for tier_dir in BENCHMARK_DIRS:
        if not tier_dir.is_dir():
            continue
        yield from tier_dir.glob("*.json")


class TestBenchmarkFixtureIntegrity:
    """Regression tests that catch the class of bug found in special-factorial-v1."""

    def test_no_fixture_has_labelled_array_expected(self):
        """
        expected must never be a 2-element list of [scalar, string].
        That pattern was the DEV-001 bug: the test-description label was
        accidentally embedded in the expected value.
        """
        bad = []
        for fixture_path in _all_benchmark_fixtures():
            data = json.loads(fixture_path.read_text())
            for tc in data.get("test_cases", []):
                exp = tc.get("expected")
                if (
                    isinstance(exp, list)
                    and len(exp) == 2
                    and isinstance(exp[0], (int, float))
                    and isinstance(exp[1], str)
                ):
                    bad.append((fixture_path.name, exp))
        assert not bad, f"Fixtures with labelled-array expected values: {bad}"

    def test_special_factorial_expected_values_are_scalars(self):
        """DEV-001 specific: all expected values must be plain ints, not lists."""
        fixture = FIXTURES_DIR / "d5" / "special-factorial-v1.json"
        data = json.loads(fixture.read_text())
        for tc in data["test_cases"]:
            assert isinstance(tc["expected"], int), (
                f"expected should be int, got {type(tc['expected'])!r}: {tc['expected']!r}"
            )

    def test_special_factorial_expected_values_correct(self):
        expected_map = {(4,): 288, (5,): 34560, (7,): 125411328000, (1,): 1}
        fixture = FIXTURES_DIR / "d5" / "special-factorial-v1.json"
        data = json.loads(fixture.read_text())
        for tc in data["test_cases"]:
            key = tuple(tc["input"])
            assert tc["expected"] == expected_map[key], (
                f"input={key}: expected {expected_map[key]}, got {tc['expected']}"
            )

    def test_benchmark_fixtures_have_function_name_metadata(self):
        """
        Fixtures with a single top-level function should declare function_name in
        metadata so the worker knows which function to call even when the participant
        defines helper functions before the main one.
        """
        missing = []
        for fixture_path in _all_benchmark_fixtures():
            data = json.loads(fixture_path.read_text())
            metadata = data.get("metadata", {})
            if not metadata.get("function_name"):
                missing.append(fixture_path.name)
        assert not missing, f"Fixtures missing metadata.function_name: {missing}"


@pytest.fixture
def participant_with_session(db):
    from agenticbrainrot.accounts.models import Participant, User
    from agenticbrainrot.consent.models import ConsentDocument, ConsentRecord

    user = User.objects.create_user(email="flag@example.com", password="pw")
    participant, _ = Participant.objects.get_or_create(user=user)
    doc = ConsentDocument.objects.create(
        version=99, title="T", body="B", is_active=True, published_at=django_tz.now()
    )
    ConsentRecord.objects.create(participant=participant, consent_document=doc, consented=True)
    participant.has_active_consent = True
    participant.profile_completed = True
    participant.save(update_fields=["has_active_consent", "profile_completed"])
    session = CodeSession.objects.create(participant=participant)
    return participant, session


@pytest.fixture
def special_factorial_challenge(db):
    return Challenge.objects.create(
        external_id="special-factorial-v1",
        title="Special Factorial",
        description="Test",
        skeleton_code="def special_factorial(n):\n    pass\n",
        test_cases=[{"input": [4], "expected": 288, "description": "Test 1"}],
        difficulty=5,
        source_metadata={"function_name": "special_factorial"},
    )


def _make_attempt(challenge, participant, session, backdate=True):
    """Create a ChallengeAttempt and optionally backdate started_at before the DEV-001 cutoff."""
    attempt = ChallengeAttempt.objects.create(
        participant=participant,
        challenge=challenge,
        session=session,
    )
    if backdate:
        ChallengeAttempt.objects.filter(pk=attempt.pk).update(
            started_at=datetime(2026, 5, 1, tzinfo=timezone.utc)
        )
        attempt.refresh_from_db()
    return attempt


class TestFlagAffectedAttempts:
    def test_dry_run_does_not_write_flags(self, special_factorial_challenge, participant_with_session):
        participant, session = participant_with_session
        attempt = _make_attempt(special_factorial_challenge, participant, session)
        call_command("flag_affected_attempts")
        attempt.refresh_from_db()
        assert attempt.data_quality_flag == ""

    def test_apply_flags_old_attempts(self, special_factorial_challenge, participant_with_session):
        participant, session = participant_with_session
        attempt = _make_attempt(special_factorial_challenge, participant, session)
        call_command("flag_affected_attempts", apply=True)
        attempt.refresh_from_db()
        assert attempt.data_quality_flag == "DEV-001"

    def test_apply_skips_attempts_after_cutoff(self, special_factorial_challenge, participant_with_session):
        participant, session = participant_with_session
        attempt = _make_attempt(special_factorial_challenge, participant, session, backdate=False)
        ChallengeAttempt.objects.filter(pk=attempt.pk).update(
            started_at=datetime(2026, 5, 26, tzinfo=timezone.utc)
        )
        call_command("flag_affected_attempts", apply=True)
        attempt.refresh_from_db()
        assert attempt.data_quality_flag == ""

    def test_apply_does_not_double_flag(self, special_factorial_challenge, participant_with_session):
        """Running the command twice doesn't change already-flagged attempts."""
        participant, session = participant_with_session
        attempt = _make_attempt(special_factorial_challenge, participant, session)
        call_command("flag_affected_attempts", apply=True)
        call_command("flag_affected_attempts", apply=True)
        attempt.refresh_from_db()
        assert attempt.data_quality_flag == "DEV-001"

    def test_already_flagged_attempt_not_reset(self, special_factorial_challenge, participant_with_session):
        """Attempts already carrying the flag are not touched by a second run."""
        participant, session = participant_with_session
        attempt = _make_attempt(special_factorial_challenge, participant, session)
        ChallengeAttempt.objects.filter(pk=attempt.pk).update(data_quality_flag="DEV-001")
        call_command("flag_affected_attempts", apply=True)
        attempt.refresh_from_db()
        assert attempt.data_quality_flag == "DEV-001"
