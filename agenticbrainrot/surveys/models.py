from django.core.exceptions import ValidationError
from django.db import models
from simple_history.models import HistoricalRecords


class SurveyQuestion(models.Model):
    """
    A survey question for profile intake, post-challenge,
    or post-session contexts.
    """

    class QuestionType(models.TextChoices):
        TEXT = "text", "Text"
        NUMBER = "number", "Number"
        SINGLE_CHOICE = "single_choice", "Single choice"
        MULTI_CHOICE = "multi_choice", "Multiple choice"
        SCALE = "scale", "Scale"

    class Context(models.TextChoices):
        PROFILE = "profile", "Profile"
        POST_CHALLENGE = "post_challenge", "Post-challenge"
        POST_SESSION = "post_session", "Post-session"
        EXIT = "exit", "Exit"

    text = models.TextField()
    help_text = models.TextField(blank=True)
    question_type = models.CharField(max_length=20, choices=QuestionType.choices)
    choices = models.JSONField(
        default=list,
        blank=True,
        help_text="Choices for single/multi_choice or scale.",
    )
    scale_min = models.IntegerField(null=True, blank=True)
    scale_max = models.IntegerField(null=True, blank=True)
    min_label = models.CharField(max_length=100, blank=True)
    max_label = models.CharField(max_length=100, blank=True)
    mid_label = models.CharField(max_length=100, blank=True)
    context = models.CharField(max_length=20, choices=Context.choices)
    category = models.CharField(max_length=100, blank=True)
    is_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ["context", "display_order"]

    def __str__(self) -> str:
        return f"[{self.context}] {self.text[:60]}"


class SurveyResponse(models.Model):
    """
    A participant's response to a survey question.
    FK rules by context:
    - profile: both session and challenge_attempt must be NULL
    - post_challenge: challenge_attempt must be set, session must be NULL
    - post_session: session must be set, challenge_attempt must be NULL
    - exit: both session and challenge_attempt must be NULL
    """

    participant = models.ForeignKey(
        "accounts.Participant",
        on_delete=models.CASCADE,
        related_name="survey_responses",
    )
    question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.PROTECT,
        related_name="responses",
    )
    value = models.TextField(blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)
    session = models.ForeignKey(
        "coding_sessions.CodeSession",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="survey_responses",
    )
    challenge_attempt = models.ForeignKey(
        "challenges.ChallengeAttempt",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="survey_responses",
    )
    supersedes = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="superseded_by",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    # profile: both null
                    models.Q(session__isnull=True, challenge_attempt__isnull=True)
                    # post_session: session set, challenge_attempt null
                    | models.Q(session__isnull=False, challenge_attempt__isnull=True)
                    # post_challenge: challenge_attempt set, session null
                    | models.Q(session__isnull=True, challenge_attempt__isnull=False)
                ),
                name="survey_response_fk_exclusivity",
            ),
        ]
        indexes = [
            models.Index(fields=["participant", "question"]),
        ]

    def __str__(self) -> str:
        return f"Response by {self.participant} to {self.question}"

    def clean(self):
        super().clean()
        context = self.question.context if self.question_id else None

        if context == SurveyQuestion.Context.PROFILE:
            if self.session_id or self.challenge_attempt_id:
                msg = (
                    "Profile responses must not reference "
                    "a session or challenge attempt."
                )
                raise ValidationError(msg)

        elif context == SurveyQuestion.Context.POST_SESSION:
            if not self.session_id:
                msg = "Post-session responses must reference a session."
                raise ValidationError(msg)
            if self.challenge_attempt_id:
                msg = "Post-session responses must not reference a challenge attempt."
                raise ValidationError(msg)

        elif context == SurveyQuestion.Context.POST_CHALLENGE:
            if not self.challenge_attempt_id:
                msg = "Post-challenge responses must reference a challenge attempt."
                raise ValidationError(msg)
            if self.session_id:
                msg = "Post-challenge responses must not reference a session."
                raise ValidationError(msg)
