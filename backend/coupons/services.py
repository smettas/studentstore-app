from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import Coupon


def validate_coupon(code, subtotal, *, lock=False):
    if not code or not str(code).strip():
        return None, Decimal("0.00")
    query = Coupon.objects.select_for_update() if lock else Coupon.objects.all()
    coupon = query.filter(code__iexact=str(code).strip()).first()
    now = timezone.now()
    if not coupon or not coupon.is_active or not (coupon.starts_at <= now < coupon.expires_at):
        raise ValidationError({"coupon_code": "Invalid or expired coupon."})
    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        raise ValidationError({"coupon_code": "Coupon usage limit reached."})
    if subtotal < coupon.minimum_order_amount:
        raise ValidationError({"coupon_code": "Minimum order value not reached."})
    if coupon.discount_type == Coupon.DiscountType.PERCENT:
        if not Decimal("0") < coupon.value <= Decimal("100"):
            raise ValidationError({"coupon_code": "Invalid percentage discount."})
        discount = subtotal * coupon.value / Decimal("100")
    else:
        if coupon.value <= 0:
            raise ValidationError({"coupon_code": "Invalid coupon amount."})
        discount = coupon.value
    if coupon.maximum_discount is not None:
        discount = min(discount, coupon.maximum_discount)
    return coupon, min(subtotal, discount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
