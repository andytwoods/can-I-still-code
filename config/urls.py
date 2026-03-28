from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.views import defaults as default_views

from agenticbrainrot.pages.api import report_client_metric
from agenticbrainrot.pages.api import stats_accuracy_by_vibe_coding
from agenticbrainrot.pages.api import stats_accuracy_over_time
from agenticbrainrot.pages.api import stats_summary
from agenticbrainrot.pages.views import AboutView
from agenticbrainrot.pages.views import CoCView
from agenticbrainrot.pages.views import HomeView
from agenticbrainrot.pages.views import PrivacyView
from agenticbrainrot.pages.views import TermsView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("about/", AboutView.as_view(), name="about"),
    path("privacy/", PrivacyView.as_view(), name="privacy"),
    path("terms/", TermsView.as_view(), name="terms"),
    path("code-of-conduct/", CoCView.as_view(), name="code_of_conduct"),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("accounts/", include("agenticbrainrot.accounts.urls", namespace="accounts")),
    path("allauth/", include("allauth.urls")),
    # Consent
    path("consent/", include("agenticbrainrot.consent.urls", namespace="consent")),
    # Surveys (profile intake)
    path("", include("agenticbrainrot.surveys.urls", namespace="surveys")),
    # Coding sessions
    path(
        "",
        include("agenticbrainrot.coding_sessions.urls", namespace="coding_sessions"),
    ),
    # Challenges
    path(
        "challenges/",
        include("agenticbrainrot.challenges.urls", namespace="challenges"),
    ),
    # Dashboard
    path(
        "",
        include("agenticbrainrot.dashboard.urls", namespace="dashboard"),
    ),
    # API
    path("api/stats/summary/", stats_summary, name="api_stats_summary"),
    path(
        "api/stats/accuracy-over-time/",
        stats_accuracy_over_time,
        name="api_stats_accuracy_over_time",
    ),
    path(
        "api/stats/accuracy-by-vibe-coding/",
        stats_accuracy_by_vibe_coding,
        name="api_stats_accuracy_by_vibe_coding",
    ),
    path(
        "api/metrics/report/",
        report_client_metric,
        name="api_report_client_metric",
    ),
    # Hijack
    path("hijack/", include("hijack.urls")),
    # Media files
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
            *urlpatterns,
        ]
