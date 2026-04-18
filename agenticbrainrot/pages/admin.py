from django.contrib import admin

from .models import PolicyDocument
from .models import Sponsor
from .models import WaitlistSignup


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


@admin.register(WaitlistSignup)
class WaitlistSignupAdmin(admin.ModelAdmin):
    list_display = ["email", "is_active", "consented_at", "notified_at", "ip_address"]
    list_filter = ["is_active"]
    search_fields = ["email"]
    readonly_fields = ["email", "consent_text", "consented_at", "ip_address", "user_agent", "unsubscribe_token"]
    ordering = ["-consented_at"]

    def has_add_permission(self, request):
        return False
