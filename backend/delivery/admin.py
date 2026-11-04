from django.contrib import admin
from .models import DeliverySettings, DeliveryPincode
@admin.register(DeliverySettings)
class DeliverySettingsAdmin(admin.ModelAdmin):
    list_display = ("id","enabled","cod_enabled","allow_all_india","estimated_min_days","estimated_max_days")
    def has_add_permission(self, request): return not DeliverySettings.objects.exists() and super().has_add_permission(request)
@admin.register(DeliveryPincode)
class DeliveryPincodeAdmin(admin.ModelAdmin):
    list_display = ("pincode","city","state","is_serviceable","cod_available","min_days","max_days")
    search_fields = ("pincode","city","state")
    list_filter = ("is_serviceable","cod_available","state")
