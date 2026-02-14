from django.contrib import admin

from .models import SurveyQuestion
from .models import SurveyResponse


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
    search_fields = ["text"]


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
