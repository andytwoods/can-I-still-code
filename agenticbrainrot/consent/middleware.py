from django.shortcuts import redirect
from django.urls import resolve


class ConsentGateMiddleware:
    """
    Redirects authenticated users who lack active consent to the consent page.
    Also checks for stale consent (document version newer than last consent).
    Exempt paths: consent page, logout, static/media, allauth, admin, hijack.
    """

    EXEMPT_URL_NAMES = {
        "consent:give_consent",
        "consent:declined",
        "account_logout",
        "surveys:profile_intake",
        "accounts:withdraw",
        "accounts:request_deletion",
    }

    EXEMPT_URL_PREFIXES = (
        "/static/",
        "/media/",
        "/allauth/",
        "/admin/",
        "/hijack/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_check(request) and self._needs_consent(request):
            return redirect("consent:give_consent")

        return self.get_response(request)

    def _should_check(self, request):
        """Return True if this request should be consent-checked."""
        if not request.user.is_authenticated:
            return False

        # Staff/superusers bypass the consent gate
        if request.user.is_staff or request.user.is_superuser:
            return False

        path = request.path

        # Exempt static/media/admin/allauth/hijack paths
        for prefix in self.EXEMPT_URL_PREFIXES:
            if path.startswith(prefix):
                return False

        # Exempt named URL patterns
        try:
            match = resolve(path)
            if match.namespace:
                url_name = f"{match.namespace}:{match.url_name}"
            else:
                url_name = match.url_name
            if url_name in self.EXEMPT_URL_NAMES:
                return False
        except Exception:  # noqa: BLE001
            return False

        return True

    def _needs_consent(self, request):
        """Check if user needs to give or renew consent."""
        from agenticbrainrot.accounts.models import Participant  # noqa: PLC0415
        from agenticbrainrot.consent.models import ConsentDocument  # noqa: PLC0415
        from agenticbrainrot.consent.models import ConsentRecord  # noqa: PLC0415

        try:
            participant = request.user.participant
        except Participant.DoesNotExist:
            return True

        # Withdrawn participants are handled elsewhere
        if participant.withdrawn_at:
            return False

        if not participant.has_active_consent:
            return True

        # Check for stale consent: is the active document newer?
        active_doc = (
            ConsentDocument.objects.filter(is_active=True)
            .order_by("-version")
            .first()
        )
        if not active_doc:
            return False

        latest_record = (
            ConsentRecord.objects.filter(
                participant=participant,
                consented=True,
            )
            .order_by("-consented_at")
            .first()
        )
        if not latest_record:
            return True

        return (
            latest_record.consent_document.version < active_doc.version
        )
