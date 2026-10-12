from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    return JsonResponse({"status": "ok", "service": "StudentStore API"})


urlpatterns = [
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
    path("api/banners/", include("banners.urls")),
    path("api/notifications/", include("notifications.urls")),
]
