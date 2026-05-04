import hashlib
import json
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import ProtectedError
from simple_history.models import HistoricalRecords


class Challenge(models.Model):
    """
    A coding challenge presented to participants.
    Never hard-delete or mutate challenges once used  -  deactivate and create a new
    row with a versioned external_id.
    """

    external_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Versioned identifier, e.g. exercism-two-fer-v1",
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    skeleton_code = models.TextField(blank=True)
    test_cases = models.JSONField(default=list)
    test_cases_hash = models.CharField(max_length=64, blank=True, editable=False)
    difficulty = models.IntegerField(
        help_text="Tier 1-5",
    )
    tags = models.JSONField(default=list, blank=True)
    source = models.JSONField(
        default=dict,
        blank=True,
        help_text="Attribution: dataset name, paper citation, license, URL.",
    )
    source_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Analysis metadata: complexity_score, function_name, etc.",
    )
    clarification = models.TextField(
        blank=True,
        default="",
        help_text="AI-generated parameter docs and worked examples. Additive only – never replaces description.",
    )
    reference_solution = models.TextField(
        blank=True,
        default="",
        help_text="Canonical solution used as timing baseline for efficiency ratio. For benchmark fixtures, drawn directly from source dataset.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(difficulty__gte=0, difficulty__lte=5),
                name="challenge_difficulty_range",
            ),
        ]
        indexes = [
            models.Index(fields=["difficulty"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        self.test_cases_hash = hashlib.sha256(
            json.dumps(self.test_cases, sort_keys=True).encode(),
        ).hexdigest()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        msg = "Challenges cannot be deleted. Deactivate instead."
        raise ProtectedError(msg, {self})


class ChallengeReport(models.Model):
    """A participant-submitted report of a problem with a challenge."""

    class Category(models.TextChoices):
        UNCLEAR_DESCRIPTION = "unclear_description", "Unclear description"
        WRONG_TEST_CASE = "wrong_test_case", "Wrong or unexpected test case"
        BROKEN_SKELETON = "broken_skeleton", "Broken skeleton code"
        OTHER = "other", "Other"

    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.PROTECT,
        related_name="reports",
    )
    participant = models.ForeignKey(
        "accounts.Participant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="challenge_reports",
    )
    category = models.CharField(max_length=50, choices=Category.choices)
    description = models.TextField()
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(
        blank=True,
        default="",
        help_text="Internal notes on how the report was resolved. Reference DEVIATIONS.md entries here.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["challenge"]),
            models.Index(fields=["resolved"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_category_display()} on {self.challenge} ({self.created_at:%Y-%m-%d})"


class ChallengeAttempt(models.Model):
    """
    A single attempt by a participant at a challenge within a session.
    Exactly one attempt per challenge per session.
    """

    participant = models.ForeignKey(
        "accounts.Participant",
        on_delete=models.CASCADE,
        related_name="challenge_attempts",
    )
    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.PROTECT,
        related_name="attempts",
    )
    session = models.ForeignKey(
        "coding_sessions.CodeSession",
        on_delete=models.CASCADE,
        related_name="challenge_attempts",
    )
    attempt_uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    submitted_code = models.TextField(blank=True)
    tests_passed = models.IntegerField(default=0)
    tests_total = models.IntegerField(default=0)
    time_taken_seconds = models.FloatField(default=0)
    active_time_seconds = models.FloatField(default=0)
    idle_time_seconds = models.FloatField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    skipped = models.BooleanField(default=False)
    think_aloud_active = models.BooleanField(default=False)
    technical_issues = models.BooleanField(default=False)
    paste_count = models.IntegerField(default=0)
    paste_total_chars = models.IntegerField(default=0)
    keystroke_count = models.IntegerField(default=0)
    tab_blur_count = models.IntegerField(default=0)
    run_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times the participant ran the code before final submission.",
    )
    complexity_metrics = models.JSONField(
        null=True,
        blank=True,
        help_text="AST-derived complexity metrics computed client-side at submission time.",
    )
    efficiency_ratio = models.FloatField(
        null=True,
        blank=True,
        help_text="Participant solution time / reference solution time. 1.0 = matched reference; >1 = slower.",
    )

    class Meta:
        unique_together = [("session", "challenge")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(tests_passed__lte=models.F("tests_total")),
                name="tests_passed_lte_total",
            ),
            models.CheckConstraint(
                condition=models.Q(time_taken_seconds__gte=0),
                name="time_taken_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(active_time_seconds__gte=0),
                name="active_time_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(idle_time_seconds__gte=0),
                name="idle_time_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(tests_passed__gte=0),
                name="tests_passed_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(paste_count__gte=0),
                name="paste_count_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(keystroke_count__gte=0),
                name="keystroke_count_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(tab_blur_count__gte=0),
                name="tab_blur_count_non_negative",
            ),
        ]
        indexes = [
            models.Index(fields=["participant"]),
            models.Index(fields=["session"]),
        ]

    def __str__(self) -> str:
        return f"{self.participant} attempt on {self.challenge}"

    def clean(self):
        super().clean()
        if self.tests_passed > self.tests_total:
            msg = "tests_passed cannot exceed tests_total."
            raise ValidationError(msg)
        if self.time_taken_seconds < 0:
            msg = "time_taken_seconds must be non-negative."
            raise ValidationError(msg)
        if self.active_time_seconds < 0:
            msg = "active_time_seconds must be non-negative."
            raise ValidationError(msg)
        if self.idle_time_seconds < 0:
            msg = "idle_time_seconds must be non-negative."
            raise ValidationError(msg)
        if self.paste_count < 0:
            msg = "paste_count must be non-negative."
            raise ValidationError(msg)
        if self.keystroke_count < 0:
            msg = "keystroke_count must be non-negative."
            raise ValidationError(msg)
        if self.tab_blur_count < 0:
            msg = "tab_blur_count must be non-negative."
            raise ValidationError(msg)
        # Cross-model: participant consistency
        if self.session_id and hasattr(self.session, "participant_id"):
            if self.participant_id != self.session.participant_id:
                msg = "ChallengeAttempt participant must match session participant."
                raise ValidationError(msg)
