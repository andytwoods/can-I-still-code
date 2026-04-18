import uuid

from django.db import models
from simple_history.models import HistoricalRecords


class PolicyDocument(models.Model):
    """Versioned policy document (privacy policy, terms, etc.)."""

    class DocType(models.TextChoices):
        PRIVACY_POLICY = "privacy_policy", "Privacy Policy"
        TERMS = "terms", "Terms of Participation"

    doc_type = models.CharField(max_length=30, choices=DocType.choices)
    version = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=255)
    body = models.TextField(help_text="Markdown content.")
    is_active = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["doc_type", "version"],
                name="unique_policy_doc_type_version",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_doc_type_display()} v{self.version}"

    @classmethod
    def get_active(cls, doc_type: str):
        """Return the active document for a given type, or None."""
        return cls.objects.filter(doc_type=doc_type, is_active=True).first()


class Sponsor(models.Model):
    """Admin-managed sponsor for display on the landing page."""

    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to="sponsors/", blank=True)
    url = models.URLField(blank=True)
    tier = models.CharField(max_length=50, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order"]

    def __str__(self) -> str:
        return self.name


class WaitlistSignup(models.Model):
    """
    Pre-registration interest for the next data collection wave.

    GDPR notes:
    - consent_text stores the exact wording shown at signup (accountability).
    - unsubscribe_token enables self-service withdrawal without authentication.
    - is_active=False is a soft delete; the record is kept as a consent audit trail.
    - notified_at is set when the wave-open email is sent; allows post-notification cleanup.
    """

    email = models.EmailField(unique=True)
    consent_text = models.TextField()
    consented_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    is_active = models.BooleanField(default=True)
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-consented_at"]

    def __str__(self) -> str:
        status = "active" if self.is_active else "unsubscribed"
        return f"{self.email} ({status})"
