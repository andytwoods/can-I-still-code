import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import Challenge
from .models import ChallengeAttempt


def export_attempts_csv(modeladmin, request, queryset):
    """Export selected challenge attempts as CSV."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=challenge_attempts.csv"
    writer = csv.writer(response)
    writer.writerow(
        [
            "participant",
            "challenge",
            "session",
            "tests_passed",
            "tests_total",
            "time_taken_seconds",
            "skipped",
            "paste_count",
            "keystroke_count",
            "tab_blur_count",
            "started_at",
        ],
    )
    for obj in queryset.select_related("challenge", "participant"):
        writer.writerow(
            [
                obj.participant,
                obj.challenge.title,
                obj.session_id,
                obj.tests_passed,
                obj.tests_total,
                obj.time_taken_seconds,
                obj.skipped,
                obj.paste_count,
                obj.keystroke_count,
                obj.tab_blur_count,
                obj.started_at,
            ],
        )
    return response


export_attempts_csv.short_description = "Export selected as CSV"


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "external_id",
        "difficulty",
        "is_active",
        "created_at",
    ]
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
        "time_taken_seconds",
        "skipped",
        "paste_count",
        "keystroke_count",
        "tab_blur_count",
        "started_at",
    ]
    list_filter = ["skipped", "challenge__difficulty"]
    search_fields = ["participant__user__email", "challenge__title"]
    readonly_fields = ["started_at", "attempt_uuid"]
    actions = [export_attempts_csv]
