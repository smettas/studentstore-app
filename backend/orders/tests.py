from decimal import Decimal
from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from accounts.models import User
from addresses.models import Address
from cart.models import Cart, CartItem
from catalog.models import Category, Product
from coupons.models import Coupon
from payments.models import Payment
from .models import Order


@override_settings(STUDENTSTORE_DELIVERY_FEE="40.00", STUDENTSTORE_FREE_DELIVERY_THRESHOLD="999.00")
class CheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(mobile="9876543210", name="Student", email="student@example.com")
        self.other = User.objects.create_user(mobile="9876543211", name="Other", email="other@example.com")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.address = Address.objects.create(user=self.user, recipient_name="Student", phone="9876543210", line1="1 Main Street", city="Bengaluru", state="Karnataka", postal_code="560001")
        self.product = Product.objects.create(name="Notebook", slug="notebook", sku="NOTE1", category=Category.objects.create(name="Books", slug="books"), price=Decimal("100.00"), stock=10)
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

    def checkout(self, **kwargs):
        return self.client.post("/api/orders/", {"address_id": self.address.pk, "payment_method": "cod", **kwargs}, format="json")

    def test_cod_checkout_and_cancel_restore_stock(self):
        result = self.checkout()
        self.assertEqual(result.status_code, 201, result.data)
        order = Order.objects.get(pk=result.data["id"])
        self.assertEqual(order.total, Decimal("240.00"))
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.payments.first().method, Payment.Method.COD)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
        self.assertFalse(CartItem.objects.filter(cart=self.cart).exists())
        self.assertEqual(self.client.post(f"/api/orders/{order.pk}/cancel/").status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)
        self.assertEqual(self.client.post(f"/api/orders/{order.pk}/cancel/").status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

    def test_reject_other_users_address(self):
        foreign = Address.objects.create(user=self.other, recipient_name="Other", phone="9876543211", line1="2 Main", city="Mysuru", state="Karnataka", postal_code="570001")
        self.assertEqual(self.checkout(address_id=foreign.pk).status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_insufficient_stock_does_not_create_order(self):
        self.product.stock = 1
        self.product.save()
        self.assertEqual(self.checkout().status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_coupon_discount_and_usage(self):
        now = timezone.now()
        coupon = Coupon.objects.create(code="SAVE10", discount_type="percent", value=10, minimum_order_amount=100, starts_at=now-timedelta(days=1), expires_at=now+timedelta(days=1))
        result = self.checkout(coupon_code="save10")
        self.assertEqual(result.status_code, 201, result.data)
        self.assertEqual(Decimal(result.data["total"]), Decimal("220.00"))
        coupon.refresh_from_db()
        self.assertEqual(coupon.used_count, 1)

    def test_orders_private(self):
        order_id = self.checkout().data["id"]
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.get(f"/api/orders/{order_id}/").status_code, 404)
        self.assertEqual(self.client.post(f"/api/orders/{order_id}/cancel/").status_code, 404)
