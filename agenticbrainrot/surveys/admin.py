import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import SurveyQuestion
from .models import SurveyResponse


def export_survey_responses_csv(modeladmin, request, queryset):
    """Export selected survey responses as CSV."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=survey_responses.csv"
    writer = csv.writer(response)
    writer.writerow(
        [
            "participant",
            "question",
            "context",
            "value",
            "session",
            "challenge_attempt",
            "answered_at",
        ],
    )
    for obj in queryset.select_related("question", "participant"):
        writer.writerow(
            [
                obj.participant,
                obj.question.text[:60],
                obj.question.context,
                obj.value,
                obj.session_id,
                obj.challenge_attempt_id,
                obj.answered_at,
            ],
        )
    return response


export_survey_responses_csv.short_description = "Export selected as CSV"


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = [
        "text",
        "question_type",
        "context",
        "display_order",
        "is_required",
        "is_active",
    ]
    list_filter = ["context", "question_type", "is_active"]
    list_editable = ["display_order", "is_active"]
    search_fields = ["text"]

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return request.user.has_perm(
            "accounts.can_edit_survey_questions",
        )

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return request.user.has_perm(
            "accounts.can_edit_survey_questions",
        )


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = [
        "participant",
        "question",
        "session",
        "challenge_attempt",
        "answered_at",
    ]
    list_filter = ["question__context", "answered_at"]
    search_fields = ["participant__user__email"]
    actions = [export_survey_responses_csv]
