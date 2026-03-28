import csv

from allauth.account.decorators import secure_admin_login
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.http import HttpResponse

from .forms import UserAdminChangeForm
from .forms import UserAdminCreationForm
from .models import AuditEvent
from .models import MetricEvent
from .models import Participant
from .models import User

if settings.DJANGO_ADMIN_FORCE_ALLAUTH:
    # Force the `admin` sign in process to go through the `django-allauth` workflow:
    # https://docs.allauth.org/en/latest/common/admin.html#admin
    admin.autodiscover()
    admin.site.login = secure_admin_login(admin.site.login)  # type: ignore[method-assign]


class ParticipantInline(admin.StackedInline):
    model = Participant
    can_delete = False
    readonly_fields = [
        "has_active_consent",
        "profile_completed",
        "profile_updated_at",
        "withdrawn_at",
        "deletion_requested_at",
        "deleted_at",
    ]


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    inlines = [ParticipantInline]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("name",)}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    list_display = ["email", "name", "is_superuser"]
    search_fields = ["name"]
    ordering = ["id"]
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )


class PendingDeletionFilter(admin.SimpleListFilter):
    title = "Pending deletion requests"
    parameter_name = "pending_deletion"

    def lookups(self, request, model_admin):
        return [("yes", "Pending deletion")]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(
                deletion_requested_at__isnull=False,
                deleted_at__isnull=True,
            )
        return queryset


def process_deletion_request(modeladmin, request, queryset):
    """Process data deletion for selected participants."""
    from agenticbrainrot.helpers.task_helpers import process_participant_deletion  # noqa: PLC0415

    processed = 0
    for participant in queryset.filter(
        deletion_requested_at__isnull=False,
        deleted_at__isnull=True,
    ):
        process_participant_deletion(participant, processed_by=request.user)
        processed += 1
    modeladmin.message_user(
        request,
        f"Processed deletion for {processed} participant(s).",
    )


process_deletion_request.short_description = "Process deletion request"


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "has_active_consent",
        "profile_completed",
        "session_count",
        "last_session_date",
        "withdrawn_at",
        "deletion_requested_at",
        "deleted_at",
    ]
    list_filter = [
        "has_active_consent",
        "profile_completed",
        PendingDeletionFilter,
    ]
    search_fields = ["user__email", "user__name"]
    actions = [process_deletion_request]

    @admin.display(description="Sessions")
    def session_count(self, obj):
        return obj.code_sessions.count()

    @admin.display(description="Last session")
    def last_session_date(self, obj):
        last = obj.code_sessions.order_by("-started_at").first()
        if last:
            return last.started_at.strftime("%d %b %Y")
        return "-"


def export_audit_events_csv(modeladmin, request, queryset):
    """Export selected audit events as CSV."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=audit_events.csv"
    writer = csv.writer(response)
    writer.writerow(["timestamp", "event_type", "participant", "actor", "metadata"])
    for event in queryset:
        writer.writerow(
            [
                event.timestamp,
                event.event_type,
                event.participant,
                event.actor,
                event.metadata,
            ],
        )
    return response


export_audit_events_csv.short_description = "Export selected as CSV"


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "event_type", "participant", "actor"]
    list_filter = ["event_type", "timestamp"]
    search_fields = ["participant__user__email"]
    readonly_fields = [
        "event_type",
        "participant",
        "actor",
        "timestamp",
        "metadata",
    ]
    actions = [export_audit_events_csv]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MetricEvent)
class MetricEventAdmin(admin.ModelAdmin):
    list_display = ["event_type", "count", "recorded_at"]
    list_filter = ["event_type", "recorded_at"]
    ordering = ["-recorded_at", "event_type"]
