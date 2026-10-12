"""Configuration checks; no network access or credentials are needed."""
from urllib.parse import urlparse

from django.conf import settings
from django.core.checks import Error, Warning, register


@register()
def check_product_media_storage(app_configs, **kwargs):
    issues = []
    provider = getattr(settings, "STUDENTSTORE_MEDIA_PROVIDER", "local")
    if provider not in {"local", "r2"}:
        issues.append(Error("Invalid STUDENTSTORE_MEDIA_PROVIDER; choose local or r2.", id="studentstore.E1201"))
    if provider != "r2":
        if not settings.DEBUG:
            issues.append(Warning(
                "Local media storage is not durable on ephemeral hosts such as Railway. Configure R2 before production uploads.",
                id="studentstore.W1201",
            ))
        return issues

    for key in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_STORAGE_BUCKET_NAME", "AWS_S3_ENDPOINT_URL", "AWS_S3_CUSTOM_DOMAIN"):
        if not getattr(settings, key, None):
            issues.append(Error(f"{key} is required for R2 media.", id="studentstore.E1202"))
    domain = getattr(settings, "AWS_S3_CUSTOM_DOMAIN", "") or ""
    if domain and ("/" in domain or ":" in domain):
        issues.append(Error("R2 public domain must be a hostname without scheme or path.", id="studentstore.E1203"))
    endpoint = getattr(settings, "AWS_S3_ENDPOINT_URL", "") or ""
    parsed = urlparse(endpoint)
    if endpoint and (parsed.scheme != "https" or not parsed.netloc):
        issues.append(Error("R2 endpoint must be an HTTPS URL.", id="studentstore.E1204"))
    return issues
