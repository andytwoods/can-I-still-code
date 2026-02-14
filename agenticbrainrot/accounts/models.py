import logging
from typing import ClassVar

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField
from django.db.models import EmailField
from django.db.models import ProtectedError
from django.urls import reverse

from .managers import UserManager

logger = logging.getLogger(__name__)


class User(AbstractUser):
    """
    Default custom user model for AgenticBrainrot.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField("Name of User", blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = EmailField("email address", unique=True)
    username = None  # type: ignore[assignment]

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    def __str__(self) -> str:
        return self.email

    def get_absolute_url(self) -> str:
        return reverse("accounts:detail", kwargs={"pk": self.id})


class Participant(models.Model):
    """
    Study-specific participant profile, created automatically via signal
    when a User is created.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="participant",
    )
    has_active_consent = models.BooleanField(default=False)
    profile_completed = models.BooleanField(default=False)
    profile_updated_at = models.DateTimeField(null=True, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    deletion_requested_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.user.email


class AuditEvent(models.Model):
    """
    Append-only audit log for user-facing critical events.
    Complements django-simple-history by recording what happened to whom and when.
    """

    class EventType(models.TextChoices):
        CONSENT_GIVEN = "consent_given", "Consent given"
        CONSENT_WITHDRAWN = "consent_withdrawn", "Consent withdrawn"
        OPTIONAL_CONSENT_GIVEN = "optional_consent_given", "Optional consent given"
        OPTIONAL_CONSENT_WITHDRAWN = (
            "optional_consent_withdrawn",
            "Optional consent withdrawn",
        )
        DELETION_REQUESTED = "deletion_requested", "Deletion requested"
        DELETION_PROCESSED = "deletion_processed", "Deletion processed"
        SESSION_STARTED = "session_started", "Session started"
        SESSION_COMPLETED = "session_completed", "Session completed"
        SESSION_ABANDONED = "session_abandoned", "Session abandoned"
        DATASET_EXPORT_RUN = "dataset_export_run", "Dataset export run"
        PROFILE_COMPLETED = "profile_completed", "Profile completed"
        WITHDRAWAL = "withdrawal", "Withdrawal"

    event_type = models.CharField(max_length=30, choices=EventType.choices)
    participant = models.ForeignKey(
        "accounts.Participant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events_as_actor",
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["event_type", "timestamp"]),
            models.Index(fields=["participant", "timestamp"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} at {self.timestamp}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            msg = "AuditEvent rows are append-only and cannot be updated."
            raise ValueError(msg)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        msg = "AuditEvent rows cannot be deleted."
        raise ProtectedError(msg, set())


def log_audit_event(
    event_type: str,
    participant=None,
    actor=None,
    **metadata,
) -> AuditEvent:
    """Helper to create an audit event."""
    return AuditEvent.objects.create(
        event_type=event_type,
        participant=participant,
        actor=actor,
        metadata=metadata,
    )
