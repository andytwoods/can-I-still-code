from django.core.signing import TimestampSigner
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from agenticbrainrot.accounts.models import AuditEvent
from agenticbrainrot.accounts.models import Participant
from agenticbrainrot.accounts.models import User
from agenticbrainrot.consent.models import OptionalConsentRecord


class TestReminderUnsubscribe(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="unsub@example.com", password="testpass123",
        )
        self.participant, _ = Participant.objects.get_or_create(
            user=self.user,
        )
        self.signer = TimestampSigner()

        # Opt in to reminders
        OptionalConsentRecord.objects.create(
            participant=self.participant,
            consent_type="reminder_emails",
            consented=True,
        )

    def test_valid_token_unsubscribes(self):
        token = self.signer.sign(str(self.participant.pk))
        url = reverse(
            "accounts:reminder_unsubscribe", kwargs={"token": token},
        )

        response = self.client.get(url)

        assert response.status_code == 200
        assert b"Unsubscribed" in response.content

        record = OptionalConsentRecord.objects.get(
            participant=self.participant,
            consent_type="reminder_emails",
        )
        assert record.consented is False
        assert record.withdrawn_at is not None

    def test_valid_token_logs_audit_event(self):
        token = self.signer.sign(str(self.participant.pk))
        url = reverse(
            "accounts:reminder_unsubscribe", kwargs={"token": token},
        )

        self.client.get(url)

        assert AuditEvent.objects.filter(
            event_type="optional_consent_withdrawn",
        ).exists()

    def test_invalid_token_shows_error(self):
        url = reverse(
            "accounts:reminder_unsubscribe",
            kwargs={"token": "invalid-token"},
        )

        response = self.client.get(url)

        assert response.status_code == 200
        assert b"Invalid" in response.content

    def test_no_login_required(self):
        """Unsubscribe should work without authentication."""
        token = self.signer.sign(str(self.participant.pk))
        url = reverse(
            "accounts:reminder_unsubscribe", kwargs={"token": token},
        )

        # No login  -  should still work
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"Unsubscribed" in response.content

    def test_already_unsubscribed_still_succeeds(self):
        """Idempotent: unsubscribing twice is fine."""
        OptionalConsentRecord.objects.filter(
            participant=self.participant,
        ).update(consented=False, withdrawn_at=timezone.now())

        token = self.signer.sign(str(self.participant.pk))
        url = reverse(
            "accounts:reminder_unsubscribe", kwargs={"token": token},
        )

        response = self.client.get(url)

        assert response.status_code == 200
        assert b"Unsubscribed" in response.content
