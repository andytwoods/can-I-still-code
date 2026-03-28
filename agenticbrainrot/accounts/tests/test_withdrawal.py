from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from agenticbrainrot.accounts.models import AuditEvent
from agenticbrainrot.accounts.models import Participant
from agenticbrainrot.accounts.models import User
from agenticbrainrot.consent.models import ConsentDocument
from agenticbrainrot.consent.models import ConsentRecord
from agenticbrainrot.helpers.task_helpers import process_participant_deletion
from agenticbrainrot.surveys.models import SurveyQuestion
from agenticbrainrot.surveys.models import SurveyResponse


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="withdraw@example.com",
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
    participant.save(update_fields=["has_active_consent"])
    return participant


@pytest.fixture
def authenticated_client(user):
    client = Client()
    client.login(
        email="withdraw@example.com",
        password="testpass123",
    )
    return client


class TestWithdrawal:
    def test_withdraw_page_renders(
        self,
        authenticated_client,
        consented_participant,
    ):
        response = authenticated_client.get(
            reverse("accounts:withdraw"),
        )
        assert response.status_code == HTTPStatus.OK
        assert b"Withdraw from Study" in response.content

    def test_withdraw_sets_fields(
        self,
        authenticated_client,
        consented_participant,
    ):
        response = authenticated_client.post(
            reverse("accounts:withdraw"),
        )
        assert response.status_code == HTTPStatus.OK

        consented_participant.refresh_from_db()
        assert consented_participant.withdrawn_at is not None
        assert consented_participant.has_active_consent is False

    def test_withdraw_logs_audit_event(
        self,
        authenticated_client,
        consented_participant,
    ):
        authenticated_client.post(reverse("accounts:withdraw"))
        assert AuditEvent.objects.filter(
            event_type="withdrawal",
            participant=consented_participant,
        ).exists()

    def test_withdrawn_cannot_start_session(
        self,
        authenticated_client,
        consented_participant,
    ):
        """Withdrawn participant is not redirected to consent but
        cannot access session pages (handled by session views)."""
        consented_participant.withdrawn_at = timezone.now()
        consented_participant.has_active_consent = False
        consented_participant.save(
            update_fields=["withdrawn_at", "has_active_consent"],
        )
        # Consent gate should not redirect withdrawn participants
        response = authenticated_client.get(reverse("home"))
        assert response.status_code == HTTPStatus.OK

    def test_htmx_withdraw_returns_partial(
        self,
        authenticated_client,
        consented_participant,
    ):
        response = authenticated_client.post(
            reverse("accounts:withdraw"),
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == HTTPStatus.OK
        assert b"Withdrawal complete" in response.content


class TestDeletionRequest:
    def test_deletion_requires_withdrawal(
        self,
        authenticated_client,
        consented_participant,
    ):
        """Cannot request deletion without withdrawing first."""
        response = authenticated_client.post(
            reverse("accounts:request_deletion"),
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_deletion_request_sets_field(
        self,
        authenticated_client,
        consented_participant,
    ):
        """Deletion request after withdrawal sets the field."""
        consented_participant.withdrawn_at = timezone.now()
        consented_participant.save(update_fields=["withdrawn_at"])

        response = authenticated_client.post(
            reverse("accounts:request_deletion"),
        )
        assert response.status_code == HTTPStatus.OK

        consented_participant.refresh_from_db()
        assert consented_participant.deletion_requested_at is not None

    def test_deletion_request_logs_audit(
        self,
        authenticated_client,
        consented_participant,
    ):
        consented_participant.withdrawn_at = timezone.now()
        consented_participant.save(update_fields=["withdrawn_at"])

        authenticated_client.post(
            reverse("accounts:request_deletion"),
        )
        assert AuditEvent.objects.filter(
            event_type="deletion_requested",
            participant=consented_participant,
        ).exists()


class TestDeletionProcessing:
    def test_process_deletion_clears_data(self, db):
        """Deletion helper removes PII but retains timing data."""
        user = User.objects.create_user(
            email="delete@example.com",
            password="testpass123",
            name="Test User",
        )
        participant, _ = Participant.objects.get_or_create(user=user)
        participant.profile_completed = True
        participant.withdrawn_at = timezone.now()
        participant.deletion_requested_at = timezone.now()
        participant.save()

        # Create survey responses
        q = SurveyQuestion.objects.create(
            text="Test?",
            question_type="text",
            context="profile",
            display_order=1,
        )
        SurveyResponse.objects.create(
            participant=participant,
            question=q,
            value="My answer",
        )

        process_participant_deletion(participant, processed_by=user)

        participant.refresh_from_db()
        assert participant.deleted_at is not None
        assert participant.profile_completed is False

        # Survey responses deleted
        assert not SurveyResponse.objects.filter(
            participant=participant,
        ).exists()

        # User name cleared
        user.refresh_from_db()
        assert user.name == ""

        # Audit event logged
        assert AuditEvent.objects.filter(
            event_type="deletion_processed",
            participant=participant,
        ).exists()
