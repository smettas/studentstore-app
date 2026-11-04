from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "sku", "quantity", "unit_price", "line_total")
    can_delete = False

class OrderStatusInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ("status", "note", "created_at")
    can_delete = False
    ordering = ("created_at", "id")

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("=id", "shipping_name", "shipping_phone")
    readonly_fields = ("created_at", "updated_at")
    inlines = [OrderItemInline, OrderStatusInline]

    def save_model(self, request, obj, form, change):
        previous = None
        if change:
            previous = Order.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
        super().save_model(request, obj, form, change)
        if change and previous != obj.status:
            OrderStatusHistory.objects.create(
                order=obj, status=obj.status,
                note="Status updated by store administrator",
            )
