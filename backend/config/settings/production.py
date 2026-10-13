"""Production-only settings for Railway (or equivalent reverse-proxy hosting)."""
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403

DEBUG = False

# No fallback to the development placeholder secret or localhost hosts in production.
if not SECRET_KEY or SECRET_KEY == "replace-this-with-a-long-random-local-secret" or len(SECRET_KEY) < 40:
    raise ImproperlyConfigured("Set a unique DJANGO_SECRET_KEY of at least 40 characters.")
if not env("DJANGO_ALLOWED_HOSTS", default="").strip():
    raise ImproperlyConfigured("Set DJANGO_ALLOWED_HOSTS to your Railway/custom domain.")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

# DATABASE_URL is injected by Railway's PostgreSQL reference variable.
# Keep separate POSTGRES_* support for alternative hosting.
DATABASE_URL = env("DATABASE_URL", default="")
if DATABASE_URL:
    DATABASES["default"] = env.db_url_config(DATABASE_URL, conn_max_age=60)
elif env("POSTGRES_PASSWORD", default="") in {"", "change-me"}:
    raise ImproperlyConfigured("Set DATABASE_URL or real POSTGRES_* database credentials.")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = env.int("DJANGO_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])
# Never allow all origins in production.
CORS_ALLOW_ALL_ORIGINS = False

# Production uploads must be durable. Railway's local filesystem is ephemeral.
if STUDENTSTORE_MEDIA_PROVIDER != "r2":
    raise ImproperlyConfigured(
        "Production requires STUDENTSTORE_MEDIA_PROVIDER=r2 with a configured R2 bucket. "
        "Keep using local settings until cloud credentials are available."
    )
