from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from agenticbrainrot.accounts.models import Participant
from agenticbrainrot.accounts.models import User
from agenticbrainrot.challenges.models import Challenge
from agenticbrainrot.challenges.models import ChallengeAttempt
from agenticbrainrot.coding_sessions.models import CodeSession
from agenticbrainrot.coding_sessions.models import CodeSessionChallenge
from agenticbrainrot.consent.models import ConsentDocument
from agenticbrainrot.consent.models import ConsentRecord


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="results@example.com",
        password="testpass123",
    )


@pytest.fixture
def participant(user):
    p, _ = Participant.objects.get_or_create(user=user)
    return p


@pytest.fixture
def consented_participant(participant):
    doc = ConsentDocument.objects.create(
        version=1,
        title="Test",
        body="Body",
        is_active=True,
        published_at=timezone.now(),
    )
    ConsentRecord.objects.create(
        participant=participant,
        consent_document=doc,
        consented=True,
    )
    participant.has_active_consent = True
    participant.profile_completed = True
    participant.save(
        update_fields=["has_active_consent", "profile_completed"],
    )
    return participant


@pytest.fixture
def logged_in_client(user):
    client = Client()
    client.login(
        email="results@example.com",
        password="testpass123",
    )
    return client


@pytest.fixture
def completed_sessions(consented_participant):
    """Create two completed sessions with attempts."""
    challenge = Challenge.objects.create(
        external_id="results-test-v1",
        title="Results Test",
        description="Test",
        skeleton_code="pass",
        test_cases=[{"input": [], "expected": True, "description": "t"}],
        difficulty=1,
    )
    sessions = []
    for i in range(2):
        session = CodeSession.objects.create(
            participant=consented_participant,
            status=CodeSession.Status.COMPLETED,
            completed_at=timezone.now(),
            challenges_attempted=1,
        )
        CodeSessionChallenge.objects.create(
            session=session,
            challenge=challenge,
            position=0,
        )
        ChallengeAttempt.objects.create(
            participant=consented_participant,
            challenge=challenge,
            session=session,
            tests_passed=1,
            tests_total=2,
            time_taken_seconds=60.0 + (i * 10),
            submitted_at=timezone.now(),
        )
        sessions.append(session)
    return sessions


class TestPersonalResults:
    def test_requires_auth(self, db):
        client = Client()
        response = client.get(reverse("dashboard:personal_results"))
        assert response.status_code == HTTPStatus.FOUND

    def test_empty_state(self, logged_in_client, consented_participant):
        response = logged_in_client.get(
            reverse("dashboard:personal_results"),
        )
        assert response.status_code == HTTPStatus.OK
        assert b"first session" in response.content

    def test_with_sessions_shows_table(
        self,
        logged_in_client,
        completed_sessions,
    ):
        response = logged_in_client.get(
            reverse("dashboard:personal_results"),
        )
        assert response.status_code == HTTPStatus.OK
        assert b"Session History" in response.content
        assert b"Session 1" in response.content
        assert b"Session 2" in response.content

    def test_with_sessions_includes_chart_data(
        self,
        logged_in_client,
        completed_sessions,
    ):
        response = logged_in_client.get(
            reverse("dashboard:personal_results"),
        )
        assert response.status_code == HTTPStatus.OK
        assert b"accuracy-chart" in response.content
        assert b"speed-chart" in response.content
        assert b"chart.js" in response.content.lower()

    def test_accuracy_calculation(
        self,
        logged_in_client,
        completed_sessions,
    ):
        """Accuracy should be 50% (1 of 2 tests passed)."""
        response = logged_in_client.get(
            reverse("dashboard:personal_results"),
        )
        assert b"50.0%" in response.content
