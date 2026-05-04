from django.db import models


class CodeSession(models.Model):
    """
    A study session during which a participant works through challenges.
    """

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        ABANDONED = "abandoned", "Abandoned"

    class DeviceType(models.TextChoices):
        DESKTOP = "desktop", "Desktop"
        LAPTOP = "laptop", "Laptop"
        TABLET = "tablet", "Tablet"
        PHONE = "phone", "Phone"

    class DistractionFree(models.TextChoices):
        YES = "yes", "Yes"
        MOSTLY = "mostly", "Mostly"
        NO = "no", "No"

    participant = models.ForeignKey(
        "accounts.Participant",
        on_delete=models.CASCADE,
        related_name="code_sessions",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    abandoned_at = models.DateTimeField(null=True, blank=True)
    challenges_attempted = models.IntegerField(default=0)
    distraction_free = models.CharField(
        max_length=10,
        choices=DistractionFree.choices,
        blank=True,
    )
    device_type = models.CharField(
        max_length=10,
        choices=DeviceType.choices,
        blank=True,
    )
    pyodide_load_ms = models.PositiveIntegerField(null=True, blank=True)
    editor_ready = models.BooleanField(default=False)
    is_mock = models.BooleanField(default=False)
    wants_harder = models.BooleanField(null=True, blank=True)
    challenges = models.ManyToManyField(
        "challenges.Challenge",
        through="CodeSessionChallenge",
        related_name="code_sessions",
    )

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(status="completed", completed_at__isnull=False) | ~models.Q(status="completed")),
                name="completed_status_requires_completed_at",
            ),
            models.CheckConstraint(
                condition=(models.Q(status="abandoned", abandoned_at__isnull=False) | ~models.Q(status="abandoned")),
                name="abandoned_status_requires_abandoned_at",
            ),
        ]
        indexes = [
            models.Index(fields=["participant", "status"]),
        ]

    def __str__(self) -> str:
        return f"Session {self.pk} for {self.participant} ({self.status})"


class CodeSessionChallenge(models.Model):
    """
    Through model tracking which challenges are assigned to a session
    and in what position.
    """

    session = models.ForeignKey(
        CodeSession,
        on_delete=models.CASCADE,
        related_name="session_challenges",
    )
    challenge = models.ForeignKey(
        "challenges.Challenge",
        on_delete=models.PROTECT,
        related_name="session_challenges",
    )
    position = models.PositiveIntegerField(default=0)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("session", "challenge")]
        ordering = ["position"]

    def __str__(self) -> str:
        return f"Challenge {self.challenge} in session {self.session.pk} (position {self.position})"
