from decimal import Decimal
from unittest.mock import patch
from django.test import SimpleTestCase
from django.test.utils import override_settings
from rest_framework.exceptions import ValidationError
from .services.razorpay_gateway import amount_in_paise
from .services.webhook_service import process_webhook


class PaymentUtilityTests(SimpleTestCase):
    def test_paise_conversion(self):
        self.assertEqual(amount_in_paise(Decimal("12.34")), 1234)

    @override_settings(RAZORPAY_WEBHOOK_SECRET="test-secret")
    def test_rejects_unsigned_webhook(self):
        with self.assertRaises(ValidationError):
            process_webhook(b'{}', "")

    @override_settings(RAZORPAY_WEBHOOK_SECRET="test-secret")
    def test_rejects_bad_signature(self):
        with self.assertRaises(ValidationError):
            process_webhook(b'{}', "bad")