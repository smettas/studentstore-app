from django.shortcuts import render
from django.db.models import Sum
from ..permissions import portal_permission
from catalog.models import Product
from orders.models import Order

@portal_permission("orders.view_order")
def index(request):
    return render(request, "staff_portal/dashboard.html", {
        "orders_count": Order.objects.count(),
        "open_orders": Order.objects.exclude(status__in=[Order.Status.CANCELLED, Order.Status.DELIVERED]).count(),
        "product_count": Product.objects.count() if request.user.has_perm("catalog.view_product") else None,
        "recent_orders": Order.objects.select_related("user").order_by("-created_at")[:10],
    })
