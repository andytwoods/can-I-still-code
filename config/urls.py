from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include
from django.urls import path
from django.views import defaults as default_views
from django.views.generic import TemplateView

from agenticbrainrot.blog.feeds import BlogFeed
from agenticbrainrot.blog.sitemaps import BlogPostSitemap
from agenticbrainrot.pages.sitemaps import StaticViewSitemap

from agenticbrainrot.pages.api import report_client_metric
from agenticbrainrot.pages.api import stats_accuracy_by_vibe_coding
from agenticbrainrot.pages.api import stats_accuracy_over_time
from agenticbrainrot.pages.api import stats_summary
from agenticbrainrot.pages.views import AboutView, VoiceDemoView, test_error
from agenticbrainrot.pages.views import CoCView
from agenticbrainrot.pages.views import HomeView
from agenticbrainrot.pages.views import HowItWorksView
from agenticbrainrot.pages.views import LoggedInHomeView
from agenticbrainrot.pages.views import PrivacyView
from agenticbrainrot.pages.views import StaffStatsView
from agenticbrainrot.pages.views import TermsView
from agenticbrainrot.pages.views import waitlist_signup
from agenticbrainrot.pages.views import waitlist_unsubscribe

_sitemaps = {
    "static": StaticViewSitemap,
    "blog": BlogPostSitemap,
}

urlpatterns = [
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain"), name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": _sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("blog/feed/", BlogFeed(), name="blog_feed"),
    path("", HomeView.as_view(), name="home"),
    path("dashboard/", LoggedInHomeView.as_view(), name="logged_in_home"),
    path("about/", AboutView.as_view(), name="about"),
    path("voice-demo/", VoiceDemoView.as_view(), name="voice_demo"),
    path("how-it-works/", HowItWorksView.as_view(), name="how_it_works"),
    path("privacy/", PrivacyView.as_view(), name="privacy"),
    path("terms/", TermsView.as_view(), name="terms"),
    path("code-of-conduct/", CoCView.as_view(), name="code_of_conduct"),
    path("waitlist/", waitlist_signup, name="waitlist_signup"),
    path("waitlist/unsubscribe/<uuid:token>/", waitlist_unsubscribe, name="waitlist_unsubscribe"),
    path("staff/stats/", StaffStatsView.as_view(), name="staff_stats"),
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
    # Blog
    path(
        "blog/",
        include("agenticbrainrot.blog.urls", namespace="blog"),
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
    # django-simple-captcha
    path("captcha/", include("captcha.urls")),
    # Hijack
    path("hijack/", include("hijack.urls")),

    # path('test-error/', test_error, name='test_error'),
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
