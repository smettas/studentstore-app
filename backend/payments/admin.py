from django.contrib import admin
from .models import Payment, PaymentWebhookEvent

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "method", "status", "amount", "created_at")
    search_fields = ("provider_order_id", "provider_payment_id")

@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("provider_event_id", "event_type", "processed_at")
