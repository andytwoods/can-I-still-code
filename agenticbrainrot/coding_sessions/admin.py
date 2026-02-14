from django.contrib import admin

from .models import CodeSession
from .models import CodeSessionChallenge


class CodeSessionChallengeInline(admin.TabularInline):
    model = CodeSessionChallenge
    extra = 0


@admin.register(CodeSession)
class CodeSessionAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "participant",
        "status",
        "started_at",
        "completed_at",
        "abandoned_at",
        "challenges_attempted",
    ]
    list_filter = ["status"]
    search_fields = ["participant__user__email"]
    inlines = [CodeSessionChallengeInline]
    readonly_fields = ["started_at"]


@admin.register(CodeSessionChallenge)
class CodeSessionChallengeAdmin(admin.ModelAdmin):
    list_display = ["session", "challenge", "position", "assigned_at"]
    list_filter = ["session__status"]
