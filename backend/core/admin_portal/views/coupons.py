from django.shortcuts import render
from coupons.models import Coupon
from ..permissions import portal_permission

@portal_permission("coupons.view_coupon")
def index(request):
    return render(request, "staff_portal/coupons.html", {"items": Coupon.objects.order_by("-expires_at")[:100]})
