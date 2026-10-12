import razorpay
from django.conf import settings
from rest_framework.exceptions import ValidationError


def client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise ValidationError({"detail": "Razorpay is not configured."})
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def amount_in_paise(amount):
    return int(amount * 100)  # Decimal amounts are stored with 2 places.
