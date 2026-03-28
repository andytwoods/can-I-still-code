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
from agenticbrainrot.consent.models import OptionalConsentRecord


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="participant@example.com",
        password="testpass123",
    )


@pytest.fixture
def participant(user):
    p, _ = Participant.objects.get_or_create(user=user)
    return p


@pytest.fixture
def consent_doc(db):
    return ConsentDocument.objects.create(
        version=1,
        title="Study Consent",
        body="# Consent\n\nYou agree to participate.",
        is_active=True,
        published_at=timezone.now(),
    )


@pytest.fixture
def authenticated_client(user):
    client = Client()
    client.login(
        email="participant@example.com",
        password="testpass123",
    )
    return client


class TestConsentGateMiddleware:
    def test_unauthenticated_user_not_redirected(self, db):
        """Anonymous users are not affected by consent gate."""
        client = Client()
        response = client.get(reverse("home"))
        assert response.status_code == HTTPStatus.OK

    def test_user_without_consent_redirected(
        self,
        authenticated_client,
        participant,
        consent_doc,
    ):
        """User without active consent is redirected."""
        response = authenticated_client.get(reverse("home"))
        assert response.status_code == HTTPStatus.FOUND
        assert reverse("consent:give_consent") in response.url

    def test_user_with_consent_not_redirected(
        self,
        authenticated_client,
        participant,
        consent_doc,
    ):
        """User with active consent can access other pages."""
        participant.has_active_consent = True
        participant.save(update_fields=["has_active_consent"])
        ConsentRecord.objects.create(
            participant=participant,
            consent_document=consent_doc,
            consented=True,
        )
        response = authenticated_client.get(reverse("home"))
        assert response.status_code == HTTPStatus.OK

    def test_consent_page_not_redirected(
        self,
        authenticated_client,
        participant,
        consent_doc,
    ):
        """Consent page itself is exempt from the gate."""
        url = reverse("consent:give_consent")
        response = authenticated_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_logout_not_redirected(
        self,
        authenticated_client,
        participant,
    ):
        """Logout URL is exempt from the gate."""
        response = authenticated_client.get(reverse("account_logout"))
        assert response.status_code == HTTPStatus.OK

    def test_stale_consent_redirected(
        self,
        authenticated_client,
        participant,
        consent_doc,
    ):
        """User with stale consent (older version) is redirected."""
        participant.has_active_consent = True
        participant.save(update_fields=["has_active_consent"])
        ConsentRecord.objects.create(
            participant=participant,
            consent_document=consent_doc,
            consented=True,
        )
        # Create a newer active document
        ConsentDocument.objects.create(
            version=2,
            title="Updated Consent",
            body="# Updated\n\nNew version.",
            is_active=True,
            published_at=timezone.now(),
        )
        response = authenticated_client.get(reverse("home"))
        assert response.status_code == HTTPStatus.FOUND
        assert reverse("consent:give_consent") in response.url

    def test_staff_bypasses_consent_gate(self, db, consent_doc):
        """Staff users bypass the consent gate."""
        User.objects.create_user(
            email="staff@example.com",
            password="testpass123",
            is_staff=True,
        )
        client = Client()
        client.login(
            email="staff@example.com",
            password="testpass123",
        )
        response = client.get(reverse("home"))
        assert response.status_code == HTTPStatus.OK


class TestConsentView:
    def test_consent_page_renders_document(
        self,
        authenticated_client,
        participant,
        consent_doc,
    ):
        """Consent page renders the active document."""
        url = reverse("consent:give_consent")
        response = authenticated_client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert b"Study Consent" in response.content
        assert b"You agree to participate" in response.content

    def test_consent_page_no_document(
        self,
        authenticated_client,
        participant,
    ):
        """If no consent doc exists, show unavailable message."""
        url = reverse("consent:give_consent")
        response = authenticated_client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert b"Consent Document Unavailable" in response.content

    def test_give_consent_creates_records(
        self,
        authenticated_client,
        participant,
        consent_doc,
    ):
        """Submitting consent creates all expected records."""
        response = authenticated_client.post(
            reverse("consent:give_consent"),
            data={
                "consent": "on",
                "reminder_emails": "on",
                "think_aloud_audio": "",
                "transcript_sharing": "on",
            },
        )
        assert response.status_code == HTTPStatus.FOUND

        # Consent record created
        record = ConsentRecord.objects.get(participant=participant)
        assert record.consented is True
        assert record.consent_document == consent_doc

        # Participant updated
        participant.refresh_from_db()
        assert participant.has_active_consent is True

        # Optional consent records created
        opt_records = OptionalConsentRecord.objects.filter(
            participant=participant,
        )
        assert opt_records.count() == len(
            OptionalConsentRecord.ConsentType.choices,
        )
        reminder = opt_records.get(consent_type="reminder_emails")
        assert reminder.consented is True
        audio = opt_records.get(consent_type="think_aloud_audio")
        assert audio.consented is False
        sharing = opt_records.get(consent_type="transcript_sharing")
        assert sharing.consented is True

        # Audit events created
        events = AuditEvent.objects.filter(participant=participant)
        consent_event = events.filter(event_type="consent_given")
        assert consent_event.exists()

        optional_events = events.filter(
            event_type="optional_consent_given",
        )
        assert optional_events.exists()

    def test_consent_without_checkbox_fails(
        self,
        authenticated_client,
        participant,
        consent_doc,
    ):
        """Submitting without consent checkbox returns errors."""
        response = authenticated_client.post(
            reverse("consent:give_consent"),
            data={},
        )
        assert response.status_code == HTTPStatus.OK
        assert b"This field is required" in response.content

    def test_decline_page_renders(
        self,
        authenticated_client,
        participant,
    ):
        """Decline page explains they can return later."""
        response = authenticated_client.get(
            reverse("consent:declined"),
        )
        assert response.status_code == HTTPStatus.OK
        assert b"welcome to return" in response.content

    def test_re_consent_after_version_update(
        self,
        authenticated_client,
        participant,
        consent_doc,
    ):
        """After new doc version, user can re-consent."""
        # First consent
        authenticated_client.post(
            reverse("consent:give_consent"),
            data={"consent": "on"},
        )
        participant.refresh_from_db()
        assert participant.has_active_consent is True

        # Create newer version
        new_doc = ConsentDocument.objects.create(
            version=2,
            title="Updated Consent",
            body="# V2\n\nUpdated terms.",
            is_active=True,
            published_at=timezone.now(),
        )

        # User should be redirected to consent again
        response = authenticated_client.get(reverse("home"))
        assert response.status_code == HTTPStatus.FOUND

        # Re-consent with new version
        response = authenticated_client.post(
            reverse("consent:give_consent"),
            data={"consent": "on"},
        )
        assert response.status_code == HTTPStatus.FOUND

        # Should now have two consent records
        records = ConsentRecord.objects.filter(
            participant=participant,
        )
        assert records.count() > 1
        latest = records.order_by("-consented_at").first()
        assert latest.consent_document == new_doc
