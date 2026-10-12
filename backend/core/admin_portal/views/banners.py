from django.shortcuts import render
from banners.models import Banner
from ..permissions import portal_permission

@portal_permission("banners.view_banner")
def index(request):
    return render(request, "staff_portal/banners.html", {"items": Banner.objects.order_by("position")[:100]})
