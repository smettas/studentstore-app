from datetime import timedelta
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone
from orders.models import Order
from payments.models import Payment
from ..permissions import portal_permission

@portal_permission("orders.view_order")
def index(request):
    since = timezone.now() - timedelta(days=30)
    # Paid revenue only. COD remains excluded until marked PAID by a verified workflow.
    paid = Payment.objects.filter(status=Payment.Status.PAID, created_at__gte=since)
    totals = paid.aggregate(gross=Sum("amount"), payments=Count("id"))
    daily = paid.annotate(day=TruncDate("created_at")).values("day").annotate(total=Sum("amount")).order_by("-day")[:30]
    return render(request, "staff_portal/reports.html", {
        "gross": totals["gross"] or 0,
        "payments": totals["payments"],
        "orders": Order.objects.filter(created_at__gte=since).count(),
        "daily": daily,
    })
