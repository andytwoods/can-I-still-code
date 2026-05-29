from django.conf import settings


def allauth_settings(request):
    """Expose some settings from django-allauth in templates."""
    return {
        "ACCOUNT_ALLOW_REGISTRATION": settings.ACCOUNT_ALLOW_REGISTRATION,
        "DOMAIN": settings.DOMAIN,
    }


def rollbar(request):
    rollbar_settings = getattr(settings, "ROLLBAR", {})
    return {
        "rollbar_client_token": getattr(settings, "ROLLBAR_CLIENT_TOKEN", ""),
        "rollbar_environment": rollbar_settings.get("environment", "development"),
    }
