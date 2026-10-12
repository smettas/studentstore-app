from django.shortcuts import render
from catalog.models import Product
from ..permissions import portal_permission

@portal_permission("catalog.view_product")
def index(request):
    q = request.GET.get("q", "").strip()[:100]
    items = Product.objects.select_related("category").order_by("name")
    if q:
        from django.db.models import Q
        items = items.filter(Q(name__icontains=q) | Q(sku__icontains=q))
    return render(request, "staff_portal/products.html", {"items": items[:100], "q": q})
