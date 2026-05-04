from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import render

from agenticbrainrot.accounts.models import Participant
from agenticbrainrot.accounts.models import log_audit_event

from .forms import ConsentForm
from .models import ConsentDocument
from .models import ConsentRecord
from .models import OptionalConsentRecord


@login_required
def give_consent(request):
    """Display consent document and handle consent form submission."""
    active_doc = ConsentDocument.objects.filter(is_active=True).order_by("-version").first()

    if not active_doc:
        return render(
            request,
            "consent/no_document.html",
            {"message": "No consent document is currently available."},
        )

    participant, _ = Participant.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ConsentForm(request.POST)
        if form.is_valid():
            # Create main consent record
            ConsentRecord.objects.create(
                participant=participant,
                consent_document=active_doc,
                consented=True,
                ip_address=_get_client_ip(request),
                user_agent=request.headers.get("user-agent", "")[:512],
            )

            # Update participant consent status
            participant.has_active_consent = True
            participant.save(update_fields=["has_active_consent"])

            # Log audit event
            log_audit_event(
                "consent_given",
                participant=participant,
                actor=request.user,
                consent_document_version=active_doc.version,
            )


            if participant.profile_completed:
                return redirect("home")
            return redirect("surveys:profile_intake")
    else:
        form = ConsentForm()

    return render(
        request,
        "consent/give_consent.html",
        {
            "document": active_doc,
            "form": form,
        },
    )


@login_required
def decline_consent(request):
    """Show a message explaining they can return later."""
    return render(request, "consent/declined.html")


def _get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
