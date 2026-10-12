from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError
from addresses.models import Address
from cart.models import Cart, CartItem
from catalog.models import Product
from coupons.models import Coupon
from coupons.services import validate_coupon
from payments.models import Payment
from .models import Order, OrderItem, OrderStatusHistory


def delivery_fee(subtotal):
    # Change via environment configuration in production.
    from decimal import InvalidOperation
    try:
        fee = Decimal(str(getattr(settings, "STUDENTSTORE_DELIVERY_FEE", "40.00")))
        threshold = Decimal(str(getattr(settings, "STUDENTSTORE_FREE_DELIVERY_THRESHOLD", "999.00")))
    except InvalidOperation:
        raise ValidationError({"detail": "Invalid delivery configuration."})
    if fee < 0 or threshold < 0:
        raise ValidationError({"detail": "Invalid delivery configuration."})
    return Decimal("0.00") if subtotal >= threshold else fee


@transaction.atomic
def create_order(*, user, address_id, coupon_code, payment_method):
    # Lock cart to prevent concurrent checkouts for the same user.
    cart = Cart.objects.select_for_update().filter(user=user).first()
    if cart is None:
        raise ValidationError({"detail": "Cart is empty."})
    address = Address.objects.filter(pk=address_id, user=user).first()
    if address is None:
        raise ValidationError({"address_id": "Address not found."})
    cart_items = list(CartItem.objects.filter(cart=cart).order_by("product_id"))
    if not cart_items:
        raise ValidationError({"detail": "Cart is empty."})
    product_ids = [item.product_id for item in cart_items]
    products = {p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids).order_by("id")}
    subtotal = Decimal("0.00")
    lines = []
    for item in cart_items:
        product = products.get(item.product_id)
        if not product or not product.is_active or item.quantity < 1 or item.quantity > product.stock:
            raise ValidationError({"detail": "Cart contains unavailable products or insufficient stock."})
        price = product.discount_price if product.discount_price is not None else product.price
        if price < 0:
            raise ValidationError({"detail": "Invalid product price."})
        amount = price * item.quantity
        subtotal += amount
        lines.append((product, item.quantity, price, amount))
    coupon, discount = validate_coupon(coupon_code, subtotal, lock=True)
    fee = delivery_fee(subtotal)
    order = Order.objects.create(
        user=user, address=address, shipping_name=address.recipient_name,
        shipping_phone=address.phone,
        shipping_address=", ".join(filter(None, [address.line1, address.line2, address.landmark, address.city, address.state, address.postal_code])),
        subtotal=subtotal, discount_total=discount, shipping_fee=fee,
        total=subtotal - discount + fee, coupon=coupon,
    )
    OrderItem.objects.bulk_create([
        OrderItem(order=order, product=p, product_name=p.name, sku=p.sku,
                  quantity=qty, unit_price=price, line_total=line_total)
        for p, qty, price, line_total in lines
    ])
    # Stock is reserved at order creation. Phase 7 must release abandoned online-payment orders.
    for product, qty, _, _ in lines:
        Product.objects.filter(pk=product.pk).update(stock=F("stock") - qty)
    if coupon:
        Coupon.objects.filter(pk=coupon.pk).update(used_count=F("used_count") + 1)
    Payment.objects.create(order=order, method=payment_method, amount=order.total)
    OrderStatusHistory.objects.create(order=order, status=order.status, note="Order created")
    CartItem.objects.filter(cart=cart).delete()
    return order


@transaction.atomic
def cancel_order(*, order_id, user):
    order = Order.objects.select_for_update().filter(pk=order_id, user=user).first()
    if not order:
        return None
    if order.status == Order.Status.CANCELLED:
        return order
    if order.status != Order.Status.PLACED:
        raise ValidationError({"detail": "Only placed orders can be cancelled."})
    if order.payments.filter(status=Payment.Status.PAID).exists():
        raise ValidationError({"detail": "Paid orders require a refund workflow; contact support."})
    for item in order.items.all().order_by("product_id"):
        Product.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)
    if order.coupon_id:
        Coupon.objects.filter(pk=order.coupon_id, used_count__gt=0).update(used_count=F("used_count") - 1)
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status", "updated_at"])
    OrderStatusHistory.objects.create(order=order, status=order.status, note="Cancelled by customer")
    return order
