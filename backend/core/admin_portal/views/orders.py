from django.shortcuts import render
from orders.models import Order
from ..permissions import portal_permission

@portal_permission("orders.view_order")
def index(request):
    status = request.GET.get("status", "")
    items = Order.objects.select_related("user").order_by("-created_at")
    if status in Order.Status.values:
        items = items.filter(status=status)
    return render(request, "staff_portal/orders.html", {"items": items[:100], "statuses": Order.Status.choices, "selected": status})
