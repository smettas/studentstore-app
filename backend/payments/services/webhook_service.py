import hashlib
import hmac
import json
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from payments.models import PaymentWebhookEvent
from .payment_service import mark_paid
from .razorpay_gateway import amount_in_paise
from payments.models import Payment


def process_webhook(raw_body, signature):
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    if not secret:
        raise ValidationError({"detail": "Webhook secret not configured."})
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    if not signature or not hmac.compare_digest(expected, signature):
        raise ValidationError({"detail": "Invalid webhook signature."})
    try:
        payload = json.loads(raw_body)
    except (ValueError, UnicodeDecodeError):
        raise ValidationError({"detail": "Invalid JSON."})
    event_id = payload.get("id")
    event_type = payload.get("event")
    if not isinstance(event_id, str) or not event_id or len(event_id) > 150:
        raise ValidationError({"detail": "Missing webhook event ID."})
    if not isinstance(event_type, str) or len(event_type) > 100:
        raise ValidationError({"detail": "Invalid event type."})
    with transaction.atomic():
        event, created = PaymentWebhookEvent.objects.get_or_create(
            provider_event_id=event_id, defaults={"event_type": event_type})
        event = PaymentWebhookEvent.objects.select_for_update().get(pk=event.pk)
        if event.processed_at:
            return "duplicate"
        if event_type == "payment.captured":
            data = payload.get("payload", {}).get("payment", {}).get("entity", {})
            provider_id, provider_order = data.get("id"), data.get("order_id")
            if not provider_id or not provider_order:
                raise ValidationError({"detail": "Missing payment identifiers."})
            payment = Payment.objects.filter(provider_order_id=provider_order, method=Payment.Method.RAZORPAY).first()
            if not payment or data.get("status") != "captured" or data.get("currency") != "INR" or data.get("amount") != amount_in_paise(payment.amount):
                raise ValidationError({"detail": "Webhook payment details mismatch."})
            mark_paid(provider_order, provider_id)
        # Unknown events are acknowledged but never change payment status.
        event.processed_at = timezone.now()
        event.save(update_fields=["processed_at"])
    return "processed"
