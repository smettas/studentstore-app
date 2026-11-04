"""Public/media R2 storage with a no-domain production fallback.

Only object keys are stored in Django fields. For the recommended proxy mode,
Django serves R2 bytes via its own public GET endpoint (no r2.dev rate limit).
For higher volume, switch to a verified R2 custom domain/CDN.
"""
from urllib.parse import quote
from django.conf import settings
from django.urls import reverse
from storages.backends.s3 import S3Storage


class PublicProductMediaStorage(S3Storage):
    default_acl = None
    querystring_auth = False
    file_overwrite = False
    location = ""

    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)
        params.setdefault("CacheControl", "public, max-age=86400")
        return params

    def url(self, name, parameters=None, expire=None, http_method=None):
        if getattr(settings, "R2_DELIVERY_MODE", "proxy") == "proxy":
            # Django absolute URL is added by DRF serializer request context.
            # No secrets or R2 service hostname are stored in product records.
            return reverse("studentstore-public-media", kwargs={"key": name})
        return super().url(name, parameters=parameters, expire=expire, http_method=http_method)
