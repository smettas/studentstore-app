from datetime import timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import Coupon
from .services import validate_coupon


class CouponTests(TestCase):
    def test_valid_coupon(self):
        now = timezone.now()
        Coupon.objects.create(code="LESS", discount_type="fixed", value=Decimal("50"), minimum_order_amount=Decimal("100"), starts_at=now-timedelta(days=1), expires_at=now+timedelta(days=1))
        _, discount = validate_coupon("less", Decimal("150"))
        self.assertEqual(discount, Decimal("50.00"))

    def test_expired_coupon(self):
        now = timezone.now()
        Coupon.objects.create(code="OLD", discount_type="fixed", value=10, starts_at=now-timedelta(days=2), expires_at=now-timedelta(days=1))
        with self.assertRaises(ValidationError):
            validate_coupon("OLD", Decimal("150"))
