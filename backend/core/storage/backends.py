"""Public Cloudflare R2 product-media storage; secrets are provided by Django settings."""
from storages.backends.s3 import S3Storage


class PublicProductMediaStorage(S3Storage):
    """Product and banner images, served from an explicitly configured public domain."""

    default_acl = None
    querystring_auth = False
    file_overwrite = False
    location = ""

    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)
        params.setdefault("CacheControl", "public, max-age=86400")
        return params
