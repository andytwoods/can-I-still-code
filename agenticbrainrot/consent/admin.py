import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import ConsentDocument
from .models import ConsentRecord
from .models import OptionalConsentRecord


def export_as_csv(modeladmin, request, queryset):
    """Export selected records as CSV."""
    meta = modeladmin.model._meta  # noqa: SLF001
    field_names = [field.name for field in meta.fields]

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={meta}.csv"
    writer = csv.writer(response)

    writer.writerow(field_names)
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in field_names])

    return response


export_as_csv.short_description = "Export selected as CSV"


@admin.register(ConsentDocument)
class ConsentDocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "version", "is_active", "published_at", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["title"]


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ["participant", "consent_document", "consented", "consented_at"]
    list_filter = ["consented", "consented_at"]
    search_fields = ["participant__user__email"]
    actions = [export_as_csv]


@admin.register(OptionalConsentRecord)
class OptionalConsentRecordAdmin(admin.ModelAdmin):
    list_display = [
        "participant",
        "consent_type",
        "consented",
        "consented_at",
        "withdrawn_at",
    ]
    list_filter = ["consent_type", "consented"]
    search_fields = ["participant__user__email"]
    actions = [export_as_csv]
