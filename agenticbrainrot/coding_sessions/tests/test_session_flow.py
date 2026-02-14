from datetime import timedelta
from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from agenticbrainrot.accounts.models import AuditEvent
from agenticbrainrot.accounts.models import Participant
from agenticbrainrot.accounts.models import User
from agenticbrainrot.challenges.models import Challenge
from agenticbrainrot.challenges.models import ChallengeAttempt
from agenticbrainrot.coding_sessions.models import CodeSession
from agenticbrainrot.coding_sessions.models import CodeSessionChallenge
from agenticbrainrot.consent.models import ConsentDocument
from agenticbrainrot.consent.models import ConsentRecord
from agenticbrainrot.surveys.models import SurveyQuestion
from agenticbrainrot.surveys.models import SurveyResponse


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="session@example.com",
        password="testpass123",  # noqa: S106
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
def challenges(db):
    """Create challenges for testing sessions."""
    return [
        Challenge.objects.create(
            external_id=f"session-test-t{tier}-{j}-v1",
            title=f"Session Test T{tier} #{j}",
            description=f"Test challenge tier {tier}",
            skeleton_code="def solution():\n    pass\n",
            test_cases=[
                {
                    "input": [],
                    "expected": True,
                    "description": "Test",
                },
            ],
            difficulty=tier,
        )
        for tier in range(1, 6)
        for j in range(3)
    ]


@pytest.fixture
def logged_in_client(user):
    client = Client()
    client.login(
        email="session@example.com",
        password="testpass123",  # noqa: S106
    )
    return client


@pytest.fixture
def session_with_challenges(consented_participant, challenges):
    """Create an in-progress session with challenges assigned."""
    session = CodeSession.objects.create(
        participant=consented_participant,
        device_type="desktop",
    )
    for i, challenge in enumerate(challenges[:3]):
        CodeSessionChallenge.objects.create(
            session=session,
            challenge=challenge,
            position=i,
        )
    return session


@pytest.fixture
def post_challenge_questions(db):
    """Create post-challenge survey questions."""
    return [
        SurveyQuestion.objects.create(
            text="How confident are you in your solution?",
            question_type="scale",
            context="post_challenge",
            scale_min=1,
            scale_max=5,
            min_label="Not at all",
            max_label="Very",
            display_order=0,
        ),
    ]


@pytest.fixture
def post_session_questions(db):
    """Create post-session survey questions."""
    return [
        SurveyQuestion.objects.create(
            text="How was the session?",
            question_type="scale",
            context="post_session",
            scale_min=1,
            scale_max=5,
            min_label="Poor",
            max_label="Great",
            display_order=0,
        ),
    ]


class TestSessionStart:
    def test_start_page_renders(
        self, logged_in_client, consented_participant, challenges,
    ):
        response = logged_in_client.get(
            reverse("coding_sessions:session_start"),
        )
        assert response.status_code == HTTPStatus.OK
        assert b"Start a Coding Session" in response.content

    def test_start_requires_auth(self, db):
        client = Client()
        response = client.get(
            reverse("coding_sessions:session_start"),
        )
        assert response.status_code == HTTPStatus.FOUND

    def test_start_requires_consent(
        self, logged_in_client, participant,
    ):
        response = logged_in_client.get(
            reverse("coding_sessions:session_start"),
        )
        assert response.status_code == HTTPStatus.FOUND

    def test_start_requires_profile(
        self, logged_in_client, participant,
    ):
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
        participant.save(update_fields=["has_active_consent"])

        response = logged_in_client.get(
            reverse("coding_sessions:session_start"),
        )
        assert response.status_code == HTTPStatus.FOUND
        assert "profile/intake" in response.url

    def test_start_creates_session(
        self, logged_in_client, consented_participant, challenges,
    ):
        response = logged_in_client.post(
            reverse("coding_sessions:session_start"),
            {"device_type": "desktop", "acknowledge": True},
        )
        assert response.status_code == HTTPStatus.FOUND
        session = CodeSession.objects.filter(
            participant=consented_participant,
        ).first()
        assert session is not None
        assert session.device_type == "desktop"
        assert session.status == CodeSession.Status.IN_PROGRESS

    def test_start_creates_session_challenges(
        self, logged_in_client, consented_participant, challenges,
    ):
        logged_in_client.post(
            reverse("coding_sessions:session_start"),
            {"device_type": "laptop", "acknowledge": True},
        )
        session = CodeSession.objects.filter(
            participant=consented_participant,
        ).first()
        assert session.session_challenges.count() > 0

    def test_start_logs_audit_event(
        self, logged_in_client, consented_participant, challenges,
    ):
        logged_in_client.post(
            reverse("coding_sessions:session_start"),
            {"device_type": "desktop", "acknowledge": True},
        )
        assert AuditEvent.objects.filter(
            event_type="session_started",
            participant=consented_participant,
        ).exists()

    def test_withdrawn_participant_blocked(
        self, logged_in_client, consented_participant, challenges,
    ):
        consented_participant.withdrawn_at = timezone.now()
        consented_participant.save(update_fields=["withdrawn_at"])

        response = logged_in_client.get(
            reverse("coding_sessions:session_start"),
        )
        assert response.status_code == HTTPStatus.OK
        assert b"withdrawn" in response.content

    def test_28_day_cooldown(
        self, logged_in_client, consented_participant, challenges,
    ):
        # Create a completed session from 10 days ago
        session = CodeSession.objects.create(
            participant=consented_participant,
            status=CodeSession.Status.COMPLETED,
            completed_at=timezone.now() - timedelta(days=10),
        )
        # Force completed_at (auto_now_add on started_at)
        session.save(update_fields=["completed_at"])

        response = logged_in_client.get(
            reverse("coding_sessions:session_start"),
        )
        assert response.status_code == HTTPStatus.OK
        assert b"cooldown" in response.content or b"recently" in response.content

    def test_cooldown_only_counts_completed(
        self, logged_in_client, consented_participant, challenges,
    ):
        """Abandoned sessions do NOT trigger the 28-day rule."""
        CodeSession.objects.create(
            participant=consented_participant,
            status=CodeSession.Status.ABANDONED,
            abandoned_at=timezone.now() - timedelta(days=1),
        )
        response = logged_in_client.get(
            reverse("coding_sessions:session_start"),
        )
        assert response.status_code == HTTPStatus.OK
        assert b"Start a Coding Session" in response.content

    def test_resumable_session(
        self, logged_in_client, session_with_challenges,
    ):
        """If an in-progress session exists, redirect to it."""
        response = logged_in_client.get(
            reverse("coding_sessions:session_start"),
        )
        assert response.status_code == HTTPStatus.FOUND
        expected_url = reverse(
            "coding_sessions:session_view",
            kwargs={"session_id": session_with_challenges.pk},
        )
        assert expected_url in response.url

    def test_stale_session_auto_abandoned(
        self, logged_in_client, consented_participant, challenges,
    ):
        """Sessions older than 4 hours are auto-abandoned."""
        old_session = CodeSession.objects.create(
            participant=consented_participant,
        )
        # Backdate the started_at
        CodeSession.objects.filter(pk=old_session.pk).update(
            started_at=timezone.now() - timedelta(hours=5),
        )

        response = logged_in_client.get(
            reverse("coding_sessions:session_start"),
        )
        old_session.refresh_from_db()
        assert old_session.status == CodeSession.Status.ABANDONED
        # Should show start page (not redirect to abandoned session)
        assert response.status_code == HTTPStatus.OK

    def test_pool_exhaustion_shows_message(
        self, logged_in_client, consented_participant,
    ):
        """When no challenges exist, show a message."""
        response = logged_in_client.post(
            reverse("coding_sessions:session_start"),
            {"device_type": "desktop", "acknowledge": True},
        )
        assert response.status_code == HTTPStatus.OK
        assert b"challenges" in response.content.lower()


class TestSessionView:
    def test_session_get_renders_challenge(
        self, logged_in_client, session_with_challenges,
    ):
        response = logged_in_client.get(
            reverse(
                "coding_sessions:session_view",
                kwargs={"session_id": session_with_challenges.pk},
            ),
        )
        assert response.status_code == HTTPStatus.OK
        assert b"Challenge 1 of 3" in response.content

    def test_submit_creates_attempt(
        self,
        logged_in_client,
        session_with_challenges,
        consented_participant,
    ):
        url = reverse(
            "coding_sessions:session_view",
            kwargs={"session_id": session_with_challenges.pk},
        )
        first_challenge = session_with_challenges.session_challenges.first()
        response = logged_in_client.post(
            url,
            {
                "action": "submit",
                "attempt_uuid": "12345678-1234-1234-1234-123456789abc",
                "submitted_code": "def solution(): return True",
                "tests_passed": "1",
                "tests_total": "1",
                "time_taken_seconds": "30.5",
                "active_time_seconds": "25.0",
                "idle_time_seconds": "5.5",
                "paste_count": "0",
                "paste_total_chars": "0",
                "keystroke_count": "50",
                "tab_blur_count": "1",
            },
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == HTTPStatus.OK
        attempt = ChallengeAttempt.objects.get(
            session=session_with_challenges,
            challenge=first_challenge.challenge,
        )
        assert attempt.tests_passed == 1
        assert attempt.submitted_code == "def solution(): return True"
        assert not attempt.skipped

    def test_submit_idempotency(
        self, logged_in_client, session_with_challenges,
    ):
        """Submitting the same attempt_uuid returns existing result."""
        url = reverse(
            "coding_sessions:session_view",
            kwargs={"session_id": session_with_challenges.pk},
        )
        attempt_uuid = "aaaa1111-2222-3333-4444-555566667777"
        data = {
            "action": "submit",
            "attempt_uuid": attempt_uuid,
            "submitted_code": "pass",
            "tests_passed": "0",
            "tests_total": "1",
            "time_taken_seconds": "10",
            "active_time_seconds": "10",
            "idle_time_seconds": "0",
            "paste_count": "0",
            "paste_total_chars": "0",
            "keystroke_count": "5",
            "tab_blur_count": "0",
        }
        # First submit
        logged_in_client.post(url, data, HTTP_HX_REQUEST="true")
        # Second submit with same UUID
        logged_in_client.post(url, data, HTTP_HX_REQUEST="true")

        # Only one attempt created
        assert ChallengeAttempt.objects.filter(
            attempt_uuid=attempt_uuid,
        ).count() == 1

    def test_skip_creates_attempt(
        self, logged_in_client, session_with_challenges,
    ):
        url = reverse(
            "coding_sessions:session_view",
            kwargs={"session_id": session_with_challenges.pk},
        )
        logged_in_client.post(
            url,
            {"action": "skip"},
            HTTP_HX_REQUEST="true",
        )
        attempt = ChallengeAttempt.objects.filter(
            session=session_with_challenges,
        ).first()
        assert attempt is not None
        assert attempt.skipped

    def test_stop_session_skips_and_shows_survey(
        self,
        logged_in_client,
        session_with_challenges,
        post_session_questions,
    ):
        url = reverse(
            "coding_sessions:session_view",
            kwargs={"session_id": session_with_challenges.pk},
        )
        response = logged_in_client.post(
            url,
            {"action": "stop"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == HTTPStatus.OK
        assert b"Post-Session Survey" in response.content
        # Current challenge was skipped
        assert ChallengeAttempt.objects.filter(
            session=session_with_challenges,
            skipped=True,
        ).exists()

    def test_submit_on_completed_session_returns_409(
        self, logged_in_client, session_with_challenges,
    ):
        session_with_challenges.status = CodeSession.Status.COMPLETED
        session_with_challenges.completed_at = timezone.now()
        session_with_challenges.save(
            update_fields=["status", "completed_at"],
        )
        url = reverse(
            "coding_sessions:session_view",
            kwargs={"session_id": session_with_challenges.pk},
        )
        response = logged_in_client.post(
            url,
            {"action": "submit", "submitted_code": "pass"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == HTTPStatus.CONFLICT

    def test_submit_on_abandoned_session_returns_409(
        self, logged_in_client, session_with_challenges,
    ):
        session_with_challenges.status = CodeSession.Status.ABANDONED
        session_with_challenges.abandoned_at = timezone.now()
        session_with_challenges.save(
            update_fields=["status", "abandoned_at"],
        )
        url = reverse(
            "coding_sessions:session_view",
            kwargs={"session_id": session_with_challenges.pk},
        )
        response = logged_in_client.post(
            url,
            {"action": "submit", "submitted_code": "pass"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == HTTPStatus.CONFLICT
        assert b"session has ended" in response.content

    def test_forbidden_for_other_user(
        self, session_with_challenges, consented_participant,
    ):
        other_user = User.objects.create_user(
            email="other2@example.com",
            password="testpass123",  # noqa: S106
        )
        other_p, _ = Participant.objects.get_or_create(user=other_user)
        doc = ConsentDocument.objects.filter(is_active=True).first()
        if doc:
            ConsentRecord.objects.create(
                participant=other_p,
                consent_document=doc,
                consented=True,
            )
        other_p.has_active_consent = True
        other_p.save(update_fields=["has_active_consent"])

        client = Client()
        client.login(
            email="other2@example.com",
            password="testpass123",  # noqa: S106
        )
        response = client.get(
            reverse(
                "coding_sessions:session_view",
                kwargs={"session_id": session_with_challenges.pk},
            ),
        )
        assert response.status_code == HTTPStatus.FORBIDDEN


class TestReflection:
    def test_reflection_shown_after_submit(
        self,
        logged_in_client,
        session_with_challenges,
        post_challenge_questions,
    ):
        url = reverse(
            "coding_sessions:session_view",
            kwargs={"session_id": session_with_challenges.pk},
        )
        response = logged_in_client.post(
            url,
            {
                "action": "submit",
                "attempt_uuid": "bbbb1111-2222-3333-4444-555566667777",
                "submitted_code": "pass",
                "tests_passed": "0",
                "tests_total": "1",
                "time_taken_seconds": "10",
                "active_time_seconds": "10",
                "idle_time_seconds": "0",
                "paste_count": "0",
                "paste_total_chars": "0",
                "keystroke_count": "5",
                "tab_blur_count": "0",
            },
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == HTTPStatus.OK
        assert b"Reflection" in response.content

    def test_reflection_submit_saves_responses(
        self,
        logged_in_client,
        session_with_challenges,
        post_challenge_questions,
        consented_participant,
    ):
        url = reverse(
            "coding_sessions:session_view",
            kwargs={"session_id": session_with_challenges.pk},
        )
        # First skip to create an attempt
        logged_in_client.post(
            url,
            {"action": "skip"},
            HTTP_HX_REQUEST="true",
        )
        attempt = ChallengeAttempt.objects.filter(
            session=session_with_challenges,
        ).first()
        q = post_challenge_questions[0]

        response = logged_in_client.post(
            url,
            {
                "action": "submit_reflection",
                "attempt_id": str(attempt.pk),
                f"question_{q.pk}": "3",
            },
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == HTTPStatus.OK
        assert SurveyResponse.objects.filter(
            participant=consented_participant,
            question=q,
            challenge_attempt=attempt,
        ).exists()

    def test_skip_reflection_shows_another_prompt(
        self,
        logged_in_client,
        session_with_challenges,
    ):
        url = reverse(
            "coding_sessions:session_view",
            kwargs={"session_id": session_with_challenges.pk},
        )
        response = logged_in_client.post(
            url,
            {"action": "skip_reflection"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == HTTPStatus.OK


class TestAnotherPrompt:
    def test_another_loads_next_challenge(
        self, logged_in_client, session_with_challenges,
    ):
        url = reverse(
            "coding_sessions:session_view",
            kwargs={"session_id": session_with_challenges.pk},
        )
        # Skip first challenge
        logged_in_client.post(
            url,
            {"action": "skip"},
            HTTP_HX_REQUEST="true",
        )
        # Request another
        response = logged_in_client.post(
            url,
            {"action": "another"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == HTTPStatus.OK

    def test_done_shows_post_session_survey(
        self,
        logged_in_client,
        session_with_challenges,
        post_session_questions,
    ):
        url = reverse(
            "coding_sessions:session_view",
            kwargs={"session_id": session_with_challenges.pk},
        )
        response = logged_in_client.post(
            url,
            {"action": "done"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == HTTPStatus.OK
        assert b"Post-Session Survey" in response.content


class TestPostSessionSurvey:
    def test_post_session_completes_session(
        self,
        logged_in_client,
        session_with_challenges,
        post_session_questions,
        consented_participant,
    ):
        url = reverse(
            "coding_sessions:session_view",
            kwargs={"session_id": session_with_challenges.pk},
        )
        q = post_session_questions[0]
        response = logged_in_client.post(
            url,
            {
                "action": "submit_post_session",
                f"question_{q.pk}": "4",
            },
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == HTTPStatus.OK
        assert response["HX-Redirect"] == "/"

        session_with_challenges.refresh_from_db()
        assert session_with_challenges.status == (
            CodeSession.Status.COMPLETED
        )
        assert session_with_challenges.completed_at is not None

    def test_post_session_logs_audit(
        self,
        logged_in_client,
        session_with_challenges,
        post_session_questions,
        consented_participant,
    ):
        url = reverse(
            "coding_sessions:session_view",
            kwargs={"session_id": session_with_challenges.pk},
        )
        q = post_session_questions[0]
        logged_in_client.post(
            url,
            {
                "action": "submit_post_session",
                f"question_{q.pk}": "4",
            },
            HTTP_HX_REQUEST="true",
        )
        assert AuditEvent.objects.filter(
            event_type="session_completed",
            participant=consented_participant,
        ).exists()

    def test_post_session_saves_responses(
        self,
        logged_in_client,
        session_with_challenges,
        post_session_questions,
        consented_participant,
    ):
        url = reverse(
            "coding_sessions:session_view",
            kwargs={"session_id": session_with_challenges.pk},
        )
        q = post_session_questions[0]
        logged_in_client.post(
            url,
            {
                "action": "submit_post_session",
                f"question_{q.pk}": "5",
            },
            HTTP_HX_REQUEST="true",
        )
        assert SurveyResponse.objects.filter(
            participant=consented_participant,
            question=q,
            session=session_with_challenges,
        ).exists()


class TestFullFlow:
    def test_complete_session_flow(
        self,
        logged_in_client,
        consented_participant,
        challenges,
        post_challenge_questions,
        post_session_questions,
    ):
        """End-to-end: start → submit → reflection → another → done → survey."""
        # Start session
        response = logged_in_client.post(
            reverse("coding_sessions:session_start"),
            {"device_type": "desktop", "acknowledge": True},
        )
        assert response.status_code == HTTPStatus.FOUND
        session = CodeSession.objects.get(
            participant=consented_participant,
            status=CodeSession.Status.IN_PROGRESS,
        )
        url = reverse(
            "coding_sessions:session_view",
            kwargs={"session_id": session.pk},
        )

        # Submit first challenge
        logged_in_client.post(
            url,
            {
                "action": "submit",
                "attempt_uuid": "cccc1111-2222-3333-4444-555566667777",
                "submitted_code": "pass",
                "tests_passed": "0",
                "tests_total": "1",
                "time_taken_seconds": "30",
                "active_time_seconds": "25",
                "idle_time_seconds": "5",
                "paste_count": "0",
                "paste_total_chars": "0",
                "keystroke_count": "20",
                "tab_blur_count": "0",
            },
            HTTP_HX_REQUEST="true",
        )

        # Skip reflection
        logged_in_client.post(
            url,
            {"action": "skip_reflection"},
            HTTP_HX_REQUEST="true",
        )

        # Done for today
        q_post = post_session_questions[0]
        logged_in_client.post(
            url,
            {"action": "done"},
            HTTP_HX_REQUEST="true",
        )

        # Submit post-session survey
        response = logged_in_client.post(
            url,
            {
                "action": "submit_post_session",
                f"question_{q_post.pk}": "4",
            },
            HTTP_HX_REQUEST="true",
        )
        assert response["HX-Redirect"] == "/"

        session.refresh_from_db()
        assert session.status == CodeSession.Status.COMPLETED
        expected_attempts = 1
        assert session.challenges_attempted == expected_attempts
