from .base import *  # noqa: F403
from .base import BASE_DIR
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env("DJANGO_SECRET_KEY")
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=["canistillcode.org", "www.canistillcode.org", "127.0.0.1", "localhost"],
)


CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "https://canistillcode.org",
        "https://www.canistillcode.org",
    ],
)

# DATABASES
# ------------------------------------------------------------------------------
DATABASES = {
    "default": env.db("DATABASE_URL"),
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)

# CACHES
# ------------------------------------------------------------------------------
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    },
}

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-name
SESSION_COOKIE_NAME = "__Secure-sessionid"
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-name
CSRF_COOKIE_NAME = "__Secure-csrftoken"
# https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
SECURE_HSTS_SECONDS = 31536000
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=True,
)
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)
# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
    "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF",
    default=True,
)

# STATIC & MEDIA
# ------------------------
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# EMAIL  -  Brevo (Sendinblue) SMTP
# ------------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp-relay.brevo.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env(
    "DJANGO_DEFAULT_FROM_EMAIL",
    default="Can I Still Code <noreply@canistillcode.org>",
)
SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
EMAIL_SUBJECT_PREFIX = env(
    "DJANGO_EMAIL_SUBJECT_PREFIX",
    default="[Can I Still CFode] ",
)
ACCOUNT_EMAIL_SUBJECT_PREFIX = EMAIL_SUBJECT_PREFIX
MFA_PASSKEY_SIGNUP_ENABLED = True

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL regex.
ADMIN_URL = env("DJANGO_ADMIN_URL", default="admin/")

# ROLLBAR
# ------------------------------------------------------------------------------
ROLLBAR_ENABLED = env.bool("ROLLBAR_ENABLED", default=False)
if ROLLBAR_ENABLED:
    ROLLBAR = {
        "access_token": env("ROLLBAR_ACCESS_TOKEN"),
        "environment": env("ROLLBAR_ENVIRONMENT", default="production"),
        "root": str(BASE_DIR),
        "branch": "master",
        "capture_ip": "anonymize",
        "scrub_fields": [
            "password",
            "passwd",
            "secret",
            "token",
            "access_token",
            "refresh_token",
            "authorization",
            "cookie",
            "sessionid",
            "csrftoken",
            "email",
            "phone",
            "address",
        ],
        "exception_level_filters": [
            ("django.http.Http404", "ignored"),
            ("django.core.exceptions.PermissionDenied", "ignored"),
        ],
        "locals": {
            "enabled": True,
            "safe_repr": True,
        },
        "suppress_re_reporting": True,
        "transform": "agenticbrainrot.utils.rollbar_utils.transform_rollbar_payload",
    }
    MIDDLEWARE += ["rollbar.contrib.django.middleware.RollbarNotifierMiddleware"]  # noqa: F405


# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(module)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.security.DisallowedHost": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": True,
        },
    },
}

# HUEY
# ------------------------------------------------------------------------------
# Override base SqliteHuey with RedisHuey for production
HUEY = {
    "huey_class": "huey.RedisHuey",
    "name": "agenticbrainrot",
    "url": REDIS_URL,
    "immediate": False,
}

# CSP
# ------------------------------------------------------------------------------
# Allow Appliku health checks and other necessary domains
if "CONTENT_SECURITY_POLICY" not in locals():
    CONTENT_SECURITY_POLICY = {
        "DIRECTIVES": {
            "default-src": ["'self'"],
            "script-src": ["'self'", "https://unpkg.com", "https://cdn.jsdelivr.net"],
            "style-src": ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
            "img-src": ["'self'", "data:"],
            "font-src": ["'self'", "https://cdn.jsdelivr.net"],
            "connect-src": ["'self'"],
            "frame-ancestors": ["'none'"],
        },
    }

CONTENT_SECURITY_POLICY["DIRECTIVES"]["connect-src"].append("https://canistillcode.org")
