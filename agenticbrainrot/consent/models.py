from django.db import models
from simple_history.models import HistoricalRecords


class ConsentDocument(models.Model):
    """
    Versioned consent document. History tracked via django-simple-history.
    """

    version = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_active = models.BooleanField(default=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ["-version"]

    def __str__(self) -> str:
        return f"{self.title} (v{self.version})"


class ConsentRecord(models.Model):
    """
    Records when a participant gave consent for a specific document.
    """

    participant = models.ForeignKey(
        "accounts.Participant",
        on_delete=models.CASCADE,
        related_name="consent_records",
    )
    consent_document = models.ForeignKey(
        ConsentDocument,
        on_delete=models.PROTECT,
        related_name="consent_records",
    )
    consented = models.BooleanField(default=True)
    consented_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["participant", "consent_document"]),
        ]

    def __str__(self) -> str:
        status = "consented" if self.consented else "declined"
        return f"Consent ({status}) for {self.participant} on {self.consent_document}"


class OptionalConsentRecord(models.Model):
    """
    Records optional consent choices (e.g., reminder emails, think-aloud audio,
    transcript sharing).
    """

    class ConsentType(models.TextChoices):
        REMINDER_EMAILS = "reminder_emails", "Reminder emails"
        THINK_ALOUD_AUDIO = "think_aloud_audio", "Think-aloud audio"
        TRANSCRIPT_SHARING = "transcript_sharing", "Transcript sharing"

    participant = models.ForeignKey(
        "accounts.Participant",
        on_delete=models.CASCADE,
        related_name="optional_consent_records",
    )
    consent_type = models.CharField(max_length=30, choices=ConsentType.choices)
    consented = models.BooleanField(default=False)
    consented_at = models.DateTimeField(auto_now_add=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["participant", "consent_type"]),
        ]

    def __str__(self) -> str:
        status = "consented" if self.consented else "declined"
        return (
            f"Optional consent ({status}) for "
            f"{self.participant}: {self.consent_type}"
        )
