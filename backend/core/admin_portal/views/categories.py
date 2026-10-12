from django.shortcuts import render
from catalog.models import Category
from ..permissions import portal_permission

@portal_permission("catalog.view_category")
def index(request):
    return render(request, "staff_portal/categories.html", {"items": Category.objects.select_related("parent").order_by("name")[:100]})
