"""Restricted streaming delivery of public catalogue images from PRIVATE R2.

Suitable at modest traffic levels without a purchased domain. This uses
Railway egress and app capacity; a custom CDN domain is recommended at scale.
"""
import mimetypes
from pathlib import PurePosixPath
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404
from django.views.decorators.http import require_GET


@require_GET
def public_media(request, key):
    if (getattr(settings, "STUDENTSTORE_MEDIA_PROVIDER", "local") != "r2"
            or getattr(settings, "R2_DELIVERY_MODE", "proxy") != "proxy"):
        raise Http404()
    if (not key or len(key) > 350 or "\\" in key or "//" in key
            or any(part in (".", "..", "") for part in key.split("/"))
            or PurePosixPath(key).is_absolute()):
        raise Http404()

    if key.startswith("products/"):
        from catalog.models import ProductImage
        visible = ProductImage.objects.filter(
            image=key, product__is_active=True, product__category__is_active=True
        ).exists()
    elif key.startswith("banners/"):
        from banners.models import Banner
        from django.utils import timezone
        now = timezone.now()
        from django.db.models import Q
        visible = Banner.objects.filter(image=key, is_active=True).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now)
        ).filter(Q(expires_at__isnull=True) | Q(expires_at__gte=now)).exists()
    else:
        visible = False
    if not visible:
        raise Http404()
    try:
        stream = default_storage.open(key, "rb")
    except Exception:
        # Avoid leaking S3 request details to clients/logs.
        raise Http404("Image unavailable")
    response = FileResponse(stream, content_type=mimetypes.guess_type(key)[0] or "application/octet-stream")
    response["Cache-Control"] = "public, max-age=3600"
    response["X-Content-Type-Options"] = "nosniff"
    return response
