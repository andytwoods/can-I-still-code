from django.contrib import admin

from .models import PolicyDocument
from .models import Sponsor


@admin.register(PolicyDocument)
class PolicyDocumentAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "doc_type",
        "version",
        "is_active",
        "published_at",
        "updated_at",
    ]
    list_filter = ["doc_type", "is_active"]
    search_fields = ["title"]
    ordering = ["doc_type", "-version"]


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ["name", "tier", "display_order", "is_active"]
    list_editable = ["display_order", "is_active"]
    list_filter = ["is_active", "tier"]
    search_fields = ["name"]
