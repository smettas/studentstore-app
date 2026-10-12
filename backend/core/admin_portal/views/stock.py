from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from catalog.models import Product
from ..forms import StockForm
from ..permissions import portal_permission

@portal_permission("catalog.change_product")
@require_http_methods(["GET", "POST"])
def index(request):
    form = StockForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=form.cleaned_data["product_id"].pk)
            product.stock = form.cleaned_data["new_stock"]
            product.save(update_fields=["stock", "updated_at"])
        messages.success(request, "Stock updated. Confirm inventory before making adjustments.")
        return redirect("staff_portal:stock")
    items = Product.objects.order_by("stock", "name")[:100]
    return render(request, "staff_portal/stock.html", {"items": items, "form": form})
