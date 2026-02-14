from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView

from agenticbrainrot.accounts.models import User
from agenticbrainrot.accounts.models import log_audit_event


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "id"
    slug_url_kwarg = "id"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["name"]
    success_message = "Information successfully updated"

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("accounts:detail", kwargs={"pk": self.request.user.pk})


user_redirect_view = UserRedirectView.as_view()


@login_required
def withdraw(request):
    """Handle participant withdrawal from the study."""
    participant = request.user.participant
    is_htmx = request.headers.get("HX-Request") == "true"

    if request.method == "POST":
        if participant.withdrawn_at:
            # Already withdrawn
            if is_htmx:
                return render(
                    request,
                    "accounts/partials/_withdrawal_status.html",
                    {"participant": participant},
                )
            return render(
                request,
                "accounts/withdrawal_complete.html",
                {"participant": participant},
            )

        # Process withdrawal
        participant.withdrawn_at = timezone.now()
        participant.has_active_consent = False
        participant.save(
            update_fields=["withdrawn_at", "has_active_consent"],
        )

        # Mark any in-progress sessions as abandoned
        from agenticbrainrot.coding_sessions.models import CodeSession  # noqa: PLC0415

        CodeSession.objects.filter(
            participant=participant,
            status="in_progress",
        ).update(
            status="abandoned",
            abandoned_at=timezone.now(),
        )

        log_audit_event(
            "withdrawal",
            participant=participant,
            actor=request.user,
        )

        if is_htmx:
            return render(
                request,
                "accounts/partials/_withdrawal_status.html",
                {"participant": participant},
            )
        return render(
            request,
            "accounts/withdrawal_complete.html",
            {"participant": participant},
        )

    # GET — show confirmation
    return render(
        request,
        "accounts/withdraw_confirm.html",
        {"participant": participant},
    )


@login_required
def request_deletion(request):
    """Handle data deletion request (only after withdrawal)."""
    participant = request.user.participant
    is_htmx = request.headers.get("HX-Request") == "true"

    if not participant.withdrawn_at:
        return HttpResponse(
            "You must withdraw before requesting deletion.",
            status=400,
        )

    if request.method == "POST":
        if not participant.deletion_requested_at:
            participant.deletion_requested_at = timezone.now()
            participant.save(update_fields=["deletion_requested_at"])

            log_audit_event(
                "deletion_requested",
                participant=participant,
                actor=request.user,
            )

        if is_htmx:
            return render(
                request,
                "accounts/partials/_deletion_status.html",
                {"participant": participant},
            )
        return render(
            request,
            "accounts/deletion_requested.html",
            {"participant": participant},
        )

    return render(
        request,
        "accounts/request_deletion.html",
        {"participant": participant},
    )
