from datetime import timedelta

from django.core import mail
from django.test import TestCase
from django.utils import timezone

from agenticbrainrot.accounts.models import AuditEvent
from agenticbrainrot.accounts.models import Participant
from agenticbrainrot.accounts.models import ReminderLog
from agenticbrainrot.accounts.models import User
from agenticbrainrot.coding_sessions.models import CodeSession
from agenticbrainrot.consent.models import ConsentRecord
from agenticbrainrot.consent.models import OptionalConsentRecord
from agenticbrainrot.helpers.task_helpers import abandon_stale_sessions
from agenticbrainrot.helpers.task_helpers import cleanup_pii_retention
from agenticbrainrot.helpers.task_helpers import send_reminder_emails


class TestAbandonStaleSessions(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        self.participant, _ = Participant.objects.get_or_create(
            user=self.user,
        )
        self.participant.has_active_consent = True
        self.participant.save()

    def test_abandons_stale_session(self):
        session = CodeSession.objects.create(
            participant=self.participant,
            status=CodeSession.Status.IN_PROGRESS,
        )
        # Backdate started_at to 5 hours ago
        CodeSession.objects.filter(pk=session.pk).update(
            started_at=timezone.now() - timedelta(hours=5),
        )

        count = abandon_stale_sessions()

        assert count == 1
        session.refresh_from_db()
        assert session.status == CodeSession.Status.ABANDONED
        assert session.abandoned_at is not None
        assert AuditEvent.objects.filter(
            event_type="session_abandoned",
        ).exists()

    def test_does_not_abandon_recent_session(self):
        CodeSession.objects.create(
            participant=self.participant,
            status=CodeSession.Status.IN_PROGRESS,
        )
        # Default started_at is now, so within timeout

        count = abandon_stale_sessions()

        assert count == 0

    def test_does_not_touch_completed_sessions(self):
        session = CodeSession.objects.create(
            participant=self.participant,
            status=CodeSession.Status.COMPLETED,
            completed_at=timezone.now() - timedelta(hours=5),
        )
        CodeSession.objects.filter(pk=session.pk).update(
            started_at=timezone.now() - timedelta(hours=10),
        )

        count = abandon_stale_sessions()

        assert count == 0


class TestSendReminderEmails(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="reminder@example.com",
            password="testpass123",
        )
        self.participant, _ = Participant.objects.get_or_create(
            user=self.user,
        )
        self.participant.has_active_consent = True
        self.participant.save()

        # Opt in to reminders
        OptionalConsentRecord.objects.create(
            participant=self.participant,
            consent_type="reminder_emails",
            consented=True,
        )

        # Create a completed session > 28 days ago
        session = CodeSession.objects.create(
            participant=self.participant,
            status=CodeSession.Status.COMPLETED,
            completed_at=timezone.now() - timedelta(days=30),
        )
        CodeSession.objects.filter(pk=session.pk).update(
            started_at=timezone.now() - timedelta(days=30),
        )

    def test_sends_reminder_to_eligible_participant(self):
        count = send_reminder_emails()

        assert count == 1
        assert len(mail.outbox) == 1
        assert "coding session" in mail.outbox[0].subject.lower()

    def test_does_not_send_to_opted_out(self):
        OptionalConsentRecord.objects.filter(
            participant=self.participant,
        ).update(consented=False)

        count = send_reminder_emails()

        assert count == 0

    def test_does_not_send_if_recent_session(self):
        CodeSession.objects.create(
            participant=self.participant,
            status=CodeSession.Status.COMPLETED,
            completed_at=timezone.now(),
        )

        count = send_reminder_emails()

        assert count == 0

    def test_no_duplicate_sends(self):
        ReminderLog.objects.create(participant=self.participant)

        count = send_reminder_emails()

        assert count == 0

    def test_does_not_send_to_withdrawn(self):
        self.participant.withdrawn_at = timezone.now()
        self.participant.save()

        count = send_reminder_emails()

        assert count == 0


class TestCleanupPiiRetention(TestCase):
    def setUp(self):
        from agenticbrainrot.consent.models import ConsentDocument  # noqa: PLC0415

        self.user = User.objects.create_user(
            email="pii@example.com",
            password="testpass123",
        )
        self.participant, _ = Participant.objects.get_or_create(
            user=self.user,
        )
        self.doc = ConsentDocument.objects.create(
            title="Test",
            body="test",
            version=1,
        )

    def test_cleans_old_records(self):
        record = ConsentRecord.objects.create(
            participant=self.participant,
            consent_document=self.doc,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        # Backdate to 25 months ago
        ConsentRecord.objects.filter(pk=record.pk).update(
            consented_at=timezone.now() - timedelta(days=25 * 30),
        )

        count = cleanup_pii_retention()

        assert count == 1
        record.refresh_from_db()
        assert record.ip_address is None
        assert record.user_agent == ""

    def test_does_not_clean_recent_records(self):
        ConsentRecord.objects.create(
            participant=self.participant,
            consent_document=self.doc,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        count = cleanup_pii_retention()

        assert count == 0
