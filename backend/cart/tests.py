from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from catalog.models import Category, Product
from .models import CartItem


class CartAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(name="Buyer", mobile="9876543210", email="buyer@example.com")
        self.client = APIClient()
        self.category = Category.objects.create(name="Books", slug="books")
        self.product = Product.objects.create(name="Guide", slug="guide", sku="G1", category=self.category, price=Decimal("100.00"), stock=3)

    def test_auth_required(self):
        self.assertIn(self.client.get("/api/cart/").status_code, (401, 403))

    def test_add_update_remove_and_stock_limit(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post("/api/cart/items/", {"product_id": self.product.pk, "quantity": 2}).status_code, 200)
        self.assertEqual(self.client.get("/api/cart/").data["total"], "200.00")
        self.assertEqual(self.client.post("/api/cart/items/", {"product_id": self.product.pk, "quantity": 2}).status_code, 400)
        item = CartItem.objects.get(cart__user=self.user)
        self.assertEqual(self.client.patch(f"/api/cart/items/{item.pk}/", {"quantity": 3}).status_code, 200)
        self.assertEqual(self.client.delete(f"/api/cart/items/{item.pk}/").status_code, 204)

    def test_cannot_delete_another_users_item(self):
        other = get_user_model().objects.create_user(name="Other", mobile="9876543211", email="other@example.com")
        self.client.force_authenticate(other)
        self.client.post("/api/cart/items/", {"product_id": self.product.pk, "quantity": 1})
        item = CartItem.objects.get(cart__user=other)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.delete(f"/api/cart/items/{item.pk}/").status_code, 404)
