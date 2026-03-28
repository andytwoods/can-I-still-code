from django.conf import settings
from django.core.cache import cache
from django.db.models import Sum
from django.views.generic import TemplateView

from agenticbrainrot.accounts.models import Participant
from agenticbrainrot.coding_sessions.models import CodeSession

from .models import PolicyDocument
from .models import Sponsor

STATS_CACHE_KEY = "landing_page_stats"
STATS_CACHE_TIMEOUT = 600  # 10 minutes


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Cached participation stats
        stats = cache.get(STATS_CACHE_KEY)
        if stats is None:
            completed_sessions = CodeSession.objects.filter(
                status=CodeSession.Status.COMPLETED,
            )
            stats = {
                "total_participants": Participant.objects.filter(
                    has_active_consent=True,
                ).count(),
                "total_sessions": completed_sessions.count(),
                "total_challenges_solved": (
                    completed_sessions.aggregate(
                        total=Sum("challenges_attempted"),
                    )["total"]
                    or 0
                ),
            }
            cache.set(STATS_CACHE_KEY, stats, STATS_CACHE_TIMEOUT)

        context["stats"] = stats
        context["sponsors"] = Sponsor.objects.filter(is_active=True)
        return context


class AboutView(TemplateView):
    template_name = "pages/about.html"


class PrivacyView(TemplateView):
    template_name = "pages/privacy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document"] = PolicyDocument.get_active(
            PolicyDocument.DocType.PRIVACY_POLICY,
        )
        return context


class TermsView(TemplateView):
    template_name = "pages/terms_and_conditions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document"] = PolicyDocument.get_active(PolicyDocument.DocType.TERMS)
        return context


class CoCView(TemplateView):
    template_name = "pages/code_of_conduct.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact_email"] = settings.ADMINS[0][1]
        return context
