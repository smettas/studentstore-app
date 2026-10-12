from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from orders.models import Order, OrderStatusHistory
from payments.models import Payment
from .razorpay_gateway import client, amount_in_paise


def owned_payment(user, order_id, method):
    payment = Payment.objects.select_related("order").filter(
        order_id=order_id, order__user=user, method=method
    ).order_by("id").first()
    if not payment:
        raise ValidationError({"detail": "Order/payment not found for this payment method."})
    return payment


def start_razorpay(user, order_id):
    payment = owned_payment(user, order_id, Payment.Method.RAZORPAY)
    if payment.order.status == Order.Status.CANCELLED or payment.status != Payment.Status.PENDING:
        raise ValidationError({"detail": "This order cannot accept a new payment."})
    if not payment.provider_order_id:
        # Gateway request is outside the DB transaction; a second check prevents overwrites.
        remote = client().order.create({"amount": amount_in_paise(payment.amount),
                                        "currency": "INR", "receipt": f"ss-{payment.pk}",
                                        "notes": {"studentstore_order_id": str(order_id)}})
        with transaction.atomic():
            locked = Payment.objects.select_for_update().select_related("order").get(pk=payment.pk)
            if locked.status != Payment.Status.PENDING or locked.order.status == Order.Status.CANCELLED:
                raise ValidationError({"detail": "Order is no longer payable."})
            if not locked.provider_order_id:
                locked.provider_order_id = remote["id"]
                locked.save(update_fields=["provider_order_id", "updated_at"])
            payment = locked
    return {"key_id": settings.RAZORPAY_KEY_ID, "razorpay_order_id": payment.provider_order_id,
            "amount": amount_in_paise(payment.amount), "currency": "INR", "order_id": order_id}


@transaction.atomic
def mark_paid(provider_order_id, provider_payment_id):
    payment = Payment.objects.select_for_update().select_related("order").filter(
        provider_order_id=provider_order_id, method=Payment.Method.RAZORPAY
    ).first()
    if not payment:
        raise ValidationError({"detail": "Unknown gateway order."})
    if payment.provider_payment_id and payment.provider_payment_id != provider_payment_id:
        raise ValidationError({"detail": "Order has another payment ID; manual review required."})
    if payment.order.status == Order.Status.CANCELLED:
        raise ValidationError({"detail": "Order was cancelled; payment requires manual refund review."})
    if payment.status == Payment.Status.PAID:
        return payment
    if payment.status != Payment.Status.PENDING:
        raise ValidationError({"detail": "Payment cannot be completed."})
    if Payment.objects.filter(provider_payment_id=provider_payment_id).exclude(pk=payment.pk).exists():
        raise ValidationError({"detail": "Payment ID already used."})
    payment.provider_payment_id = provider_payment_id
    payment.status = Payment.Status.PAID
    payment.save(update_fields=["provider_payment_id", "status", "updated_at"])
    order = payment.order
    if order.status == Order.Status.PLACED:
        order.status = Order.Status.CONFIRMED
        order.save(update_fields=["status", "updated_at"])
        OrderStatusHistory.objects.create(order=order, status=order.status, note="Razorpay payment confirmed")
    return payment


def verify_razorpay(user, data):
    payment = owned_payment(user, data["order_id"], Payment.Method.RAZORPAY)
    if not payment.provider_order_id or payment.provider_order_id != data["razorpay_order_id"]:
        raise ValidationError({"detail": "Razorpay order mismatch."})
    gateway = client()
    try:
        gateway.utility.verify_payment_signature({
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"]})
        remote = gateway.payment.fetch(data["razorpay_payment_id"])
    except Exception:
        raise ValidationError({"detail": "Payment verification failed."})
    if (remote.get("order_id") != payment.provider_order_id or
            remote.get("status") != "captured" or remote.get("currency") != "INR" or
            remote.get("amount") != amount_in_paise(payment.amount)):
        raise ValidationError({"detail": "Payment not captured or amount mismatch."})
    return mark_paid(payment.provider_order_id, data["razorpay_payment_id"])


@transaction.atomic
def confirm_cod(user, order_id):
    payment = Payment.objects.select_for_update().select_related("order").filter(
        order_id=order_id, order__user=user, method=Payment.Method.COD).first()
    if not payment or payment.order.status == Order.Status.CANCELLED:
        raise ValidationError({"detail": "COD order not found or cancelled."})
    if payment.status != Payment.Status.PENDING:
        raise ValidationError({"detail": "COD order is not pending."})
    if payment.order.status == Order.Status.PLACED:
        payment.order.status = Order.Status.CONFIRMED
        payment.order.save(update_fields=["status", "updated_at"])
        OrderStatusHistory.objects.create(order=payment.order, status=Order.Status.CONFIRMED,
                                          note="Cash on delivery confirmed; collect on delivery")
    # COD remains PENDING until cash is collected; never mark it PAID here.
    return payment
