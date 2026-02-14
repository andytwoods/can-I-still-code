from django.contrib import admin

from .models import Challenge
from .models import ChallengeAttempt


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ["title", "external_id", "difficulty", "is_active", "created_at"]
    list_filter = ["difficulty", "is_active"]
    search_fields = ["title", "external_id", "description"]
    readonly_fields = ["test_cases_hash"]


@admin.register(ChallengeAttempt)
class ChallengeAttemptAdmin(admin.ModelAdmin):
    list_display = [
        "participant",
        "challenge",
        "session",
        "tests_passed",
        "tests_total",
        "skipped",
        "started_at",
    ]
    list_filter = ["skipped", "challenge__difficulty"]
    search_fields = ["participant__user__email", "challenge__title"]
    readonly_fields = ["started_at", "attempt_uuid"]
