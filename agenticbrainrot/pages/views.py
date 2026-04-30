import json
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import TemplateView
from django_ratelimit.decorators import ratelimit

from agenticbrainrot.accounts.models import Participant
from agenticbrainrot.coding_sessions.models import CodeSession
from agenticbrainrot.coding_sessions.views import _abandon_stale_sessions

from .forms import WAITLIST_CONSENT_TEXT
from .forms import WaitlistSignupForm
from .models import WaitlistSignup

from .models import PolicyDocument
from .models import Sponsor

STATS_CACHE_KEY = "landing_page_stats"
STATS_CACHE_TIMEOUT = 600  # 10 minutes

# Okabe-Ito palette (matches dashboard)
_CHART_COLOURS = {
    "accuracy": "rgb(0, 114, 178)",
    "speed": "rgb(230, 159, 0)",
    "runs": "rgb(0, 158, 115)",
    "accuracy_bg": "rgba(0, 114, 178, 0.1)",
    "speed_bg": "rgba(230, 159, 0, 0.1)",
    "runs_bg": "rgba(0, 158, 115, 0.1)",
}

# Demo trajectory: accuracy drifts down, time and runs drift up over 6 sessions
_DEMO_SESSIONS = [
    (0,   88.0, 42.0, 2.1),
    (28,  85.0, 46.0, 2.4),
    (59,  83.0, 49.0, 2.6),
    (89,  79.0, 54.0, 3.0),
    (120, 75.0, 61.0, 3.4),
    (151, 71.0, 68.0, 3.8),
]


def _demo_chart_data():
    """Return demo accuracy/speed/runs data anchored to today minus ~5 months."""
    anchor = timezone.now() - timedelta(days=151)
    accuracy, speed, runs = [], [], []
    for days_offset, acc, spd, run in _DEMO_SESSIONS:
        x = (anchor + timedelta(days=days_offset)).isoformat()
        accuracy.append({"x": x, "y": acc})
        speed.append({"x": x, "y": spd})
        runs.append({"x": x, "y": run})
    return accuracy, speed, runs

def test_error(request):
    raise(AttributeError('raised as part of rollbar test'))


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("logged_in_home")
        return super().get(request, *args, **kwargs)

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
        context["contact_email"] = settings.ADMINS[0][1]

        acc, spd, runs = _demo_chart_data()
        context["accuracy_data"] = json.dumps(acc)
        context["speed_data"] = json.dumps(spd)
        context["runs_data"] = json.dumps(runs)
        context["chart_colours"] = json.dumps(_CHART_COLOURS)
        return context


class LoggedInHomeView(LoginRequiredMixin, TemplateView):
    template_name = "pages/logged_in_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        try:
            participant = Participant.objects.get(user=user)
        except Participant.DoesNotExist:
            # Staff users without a participant record
            context["no_participant"] = True
            return context

        _abandon_stale_sessions(participant)

        cooldown_days = settings.STUDY["SESSION_COOLDOWN_DAYS"]

        active_session = CodeSession.objects.filter(
            participant=participant,
            status=CodeSession.Status.IN_PROGRESS,
            is_mock=False,
        ).first()

        last_completed = (
            CodeSession.objects.filter(
                participant=participant,
                status=CodeSession.Status.COMPLETED,
                is_mock=False,
            )
            .order_by("-completed_at")
            .first()
        )

        next_eligible = None
        if active_session:
            session_status = "active"
        elif last_completed and last_completed.completed_at:
            next_eligible_dt = last_completed.completed_at + timezone.timedelta(days=cooldown_days)
            if timezone.now() < next_eligible_dt:
                session_status = "cooldown"
                next_eligible = next_eligible_dt
            else:
                session_status = "ready"
        else:
            session_status = "ready"

        completed_sessions_count = CodeSession.objects.filter(
            participant=participant,
            status=CodeSession.Status.COMPLETED,
            is_mock=False,
        ).count()

        context.update(
            {
                "participant": participant,
                "active_session": active_session,
                "session_status": session_status,
                "next_eligible": next_eligible,
                "completed_sessions_count": completed_sessions_count,
            }
        )
        return context


class AboutView(TemplateView):
    template_name = "pages/about.html"


class HowItWorksView(TemplateView):
    template_name = "pages/how_it_works.html"


class PrivacyView(TemplateView):
    template_name = "pages/privacy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document"] = PolicyDocument.get_active(
            PolicyDocument.DocType.PRIVACY_POLICY,
        )
        context["privacy_email"] = settings.PRIVACY_EMAIL
        return context


class TermsView(TemplateView):
    template_name = "pages/terms_and_conditions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document"] = PolicyDocument.get_active(PolicyDocument.DocType.TERMS)
        context["contact_email"] = settings.CONTACT_EMAIL
        return context


class CoCView(TemplateView):
    template_name = "pages/code_of_conduct.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact_email"] = settings.ADMINS[0][1]
        return context


def _get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _send_waitlist_acknowledgement(signup, request):
    unsubscribe_url = request.build_absolute_uri(
        f"/waitlist/unsubscribe/{signup.unsubscribe_token}/"
    )
    subject = "You're on the waitlist – Can I Still Code"
    body = (
        f"Hi,\n\n"
        f"You've signed up to be notified when the next data collection wave of "
        f"the Can I Still Code study opens. We'll send you a single email when "
        f"registration becomes available.\n\n"
        f"If you didn't sign up, or you'd like to remove yourself from the waitlist, "
        f"click the link below — no account needed:\n\n"
        f"{unsubscribe_url}\n\n"
        f"– The Can I Still Code team\n"
        f"canistillcode.org\n"
    )
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.CONTACT_EMAIL,
        recipient_list=[signup.email],
        fail_silently=True,
    )


@ratelimit(key="ip", rate="5/h", method="POST", block=False)
def waitlist_signup(request):
    if getattr(request, "limited", False):
        return render(request, "pages/waitlist.html", {
            "form": WaitlistSignupForm(),
            "rate_limited": True,
        }, status=429)

    if request.method == "POST":
        form = WaitlistSignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            existing = WaitlistSignup.objects.filter(email=email).first()
            if existing:
                if not existing.is_active:
                    # Reactivate if they previously unsubscribed
                    existing.is_active = True
                    existing.consent_text = WAITLIST_CONSENT_TEXT
                    existing.ip_address = _get_client_ip(request)
                    existing.user_agent = request.META.get("HTTP_USER_AGENT", "")[:512]
                    existing.save()
                    _send_waitlist_acknowledgement(existing, request)
                messages.info(
                    request,
                    "You're already on the waitlist. Check your inbox for the acknowledgement "
                    "email — it contains an unsubscribe link if you change your mind.",
                )
            else:
                signup = WaitlistSignup.objects.create(
                    email=email,
                    consent_text=WAITLIST_CONSENT_TEXT,
                    ip_address=_get_client_ip(request),
                    user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
                )
                _send_waitlist_acknowledgement(signup, request)
                messages.success(
                    request,
                    "You're on the list. We've sent a confirmation to your email address "
                    "with an unsubscribe link.",
                )
            return redirect("waitlist_signup")
    else:
        form = WaitlistSignupForm()

    return render(request, "pages/waitlist.html", {"form": form})


def waitlist_unsubscribe(request, token):
    signup = get_object_or_404(WaitlistSignup, unsubscribe_token=token)
    if request.method == "POST":
        signup.is_active = False
        signup.save()
        return render(request, "pages/waitlist_unsubscribe.html", {"signup": signup, "done": True})
    return render(request, "pages/waitlist_unsubscribe.html", {"signup": signup, "done": False})
