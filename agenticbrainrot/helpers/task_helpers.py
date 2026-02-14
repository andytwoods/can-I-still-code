from django.utils import timezone

from agenticbrainrot.accounts.models import log_audit_event


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
