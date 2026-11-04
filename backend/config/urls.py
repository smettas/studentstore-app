from django.contrib import admin
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.urls import include, path
from core.storage.media_proxy import public_media


@require_GET
def health_check(request):
    return JsonResponse({"status": "ok", "service": "StudentStore API"})


urlpatterns = [
    path("api/media/<path:key>", public_media, name="studentstore-public-media"),
    path("admin/", admin.site.urls),
    path("staff/", include("core.admin_portal.urls")),
    path("api/health/", health_check, name="health-check"),
    path("api/accounts/", include("accounts.urls")),
    path("api/catalog/", include("catalog.urls")),
    path("api/cart/", include("cart.urls")),
    path("api/wishlist/", include("wishlist.urls")),
    path("api/addresses/", include("addresses.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/coupons/", include("coupons.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/delivery/", include("delivery.urls")),
    path("api/banners/", include("banners.urls")),
    path("api/notifications/", include("notifications.urls")),
]

# Serve uploaded catalogue images from the development server only.
from django.conf import settings
from django.conf.urls.static import static
if settings.DEBUG and settings.STUDENTSTORE_MEDIA_PROVIDER == 'local':
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
