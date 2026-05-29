from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class CanonicalHostMiddleware:
    """
    Redirect alternate hosts to the canonical host.

    Example:
    https://www.canistillcode.org/foo/?x=1
    -> https://canistillcode.org/foo/?x=1
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.canonical_host = getattr(settings, "CANONICAL_HOST", "")
        self.redirect_hosts = set(getattr(settings, "CANONICAL_REDIRECT_HOSTS", []))

    def __call__(self, request):
        host = request.get_host().split(":")[0]

        if host in self.redirect_hosts:
            new_url = f"https://{self.canonical_host}{request.get_full_path()}"
            return HttpResponsePermanentRedirect(new_url)

        return self.get_response(request)
