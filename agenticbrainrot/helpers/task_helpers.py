import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.signing import TimestampSigner
from django.utils import timezone

from agenticbrainrot.accounts.models import log_audit_event

logger = logging.getLogger(__name__)


def process_participant_deletion(participant, processed_by=None):
    """
    Process a participant data deletion request.

    Deletes PII while retaining anonymised timing/accuracy data
    and consent audit log.

    - Deletes SurveyResponse rows
    - Blanks ChallengeAttempt.submitted_code
    - Deletes OptionalConsentRecord rows
    - Sets Participant.deleted_at

    Retains: ConsentRecord (audit log), ChallengeAttempt timing data.
    """
    from agenticbrainrot.challenges.models import ChallengeAttempt  # noqa: PLC0415
    from agenticbrainrot.consent.models import OptionalConsentRecord  # noqa: PLC0415
    from agenticbrainrot.surveys.models import SurveyResponse  # noqa: PLC0415

    # Delete survey responses (PII)
    SurveyResponse.objects.filter(participant=participant).delete()

    # Blank submitted code in challenge attempts (retain timing data)
    ChallengeAttempt.objects.filter(participant=participant).update(
        submitted_code="",
    )

    # Delete optional consent records
    OptionalConsentRecord.objects.filter(participant=participant).delete()

    # Clear profile fields
    participant.profile_completed = False
    participant.profile_updated_at = None
    participant.deleted_at = timezone.now()
    participant.save(
        update_fields=[
            "profile_completed",
            "profile_updated_at",
            "deleted_at",
        ],
    )

    # Clear user PII
    user = participant.user
    user.name = ""
    user.save(update_fields=["name"])

    log_audit_event(
        "deletion_processed",
        participant=participant,
        actor=processed_by,
    )


def abandon_stale_sessions():
    """Mark in-progress sessions older than SESSION_TIMEOUT_HOURS as abandoned."""
    from agenticbrainrot.coding_sessions.models import CodeSession  # noqa: PLC0415

    timeout_hours = settings.STUDY["SESSION_TIMEOUT_HOURS"]
    cutoff = timezone.now() - timedelta(hours=timeout_hours)

    stale = CodeSession.objects.filter(
        status=CodeSession.Status.IN_PROGRESS,
        started_at__lt=cutoff,
    )
    count = 0
    for session in stale:
        session.status = CodeSession.Status.ABANDONED
        session.abandoned_at = timezone.now()
        session.save(update_fields=["status", "abandoned_at"])
        log_audit_event(
            "session_abandoned",
            participant=session.participant,
            session_id=session.pk,
        )
        count += 1

    if count:
        logger.info("Abandoned %d stale sessions", count)
    return count


def send_reminder_emails():
    """Send reminder emails to eligible participants."""
    from agenticbrainrot.accounts.models import Participant  # noqa: PLC0415
    from agenticbrainrot.accounts.models import ReminderLog  # noqa: PLC0415
    from agenticbrainrot.coding_sessions.models import CodeSession  # noqa: PLC0415
    from agenticbrainrot.consent.models import OptionalConsentRecord  # noqa: PLC0415

    cooldown_days = settings.STUDY["SESSION_COOLDOWN_DAYS"]
    cutoff = timezone.now() - timedelta(days=cooldown_days)
    signer = TimestampSigner()

    # Find participants opted in for reminders
    opted_in_ids = set(
        OptionalConsentRecord.objects.filter(
            consent_type="reminder_emails",
            consented=True,
            withdrawn_at__isnull=True,
        ).values_list("participant_id", flat=True),
    )

    if not opted_in_ids:
        return 0

    # Filter eligible participants
    participants = Participant.objects.filter(
        pk__in=opted_in_ids,
        has_active_consent=True,
        withdrawn_at__isnull=True,
        deleted_at__isnull=True,
    )

    sent = 0
    for participant in participants:
        # Check last completed session > 28 days ago
        last_session = (
            CodeSession.objects.filter(
                participant=participant,
                status=CodeSession.Status.COMPLETED,
            )
            .order_by("-completed_at")
            .first()
        )
        if last_session and last_session.completed_at > cutoff:
            continue

        # Check no reminder in last 28 days
        recent_reminder = ReminderLog.objects.filter(
            participant=participant,
            sent_at__gt=cutoff,
        ).exists()
        if recent_reminder:
            continue

        # Generate unsubscribe token
        token = signer.sign(str(participant.pk))
        unsubscribe_path = f"/accounts/reminders/unsubscribe/{token}/"

        email = EmailMessage(
            subject="Ready for your next coding session?",
            body=(
                "It's been a while  -  ready for your next coding session?\n\n"
                "Visit the app to start a new session.\n\n"
                "To unsubscribe from reminders:\n"
                f"  {unsubscribe_path}\n"
            ),
            to=[participant.user.email],
            headers={"List-Unsubscribe": f"<{unsubscribe_path}>"},
        )
        email.send(fail_silently=True)

        ReminderLog.objects.create(participant=participant)
        sent += 1

    if sent:
        logger.info("Sent %d reminder emails", sent)
    return sent


def cleanup_pii_retention():
    """Purge PII from consent records older than 24 months."""
    from agenticbrainrot.consent.models import ConsentRecord  # noqa: PLC0415

    retention_months = 24
    cutoff = timezone.now() - timedelta(days=retention_months * 30)

    updated = ConsentRecord.objects.filter(
        consented_at__lt=cutoff,
        ip_address__isnull=False,
    ).update(ip_address=None, user_agent="")

    if updated:
        logger.info("Cleaned PII from %d consent records", updated)
    return updated
