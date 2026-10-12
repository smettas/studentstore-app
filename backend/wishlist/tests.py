from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from catalog.models import Category, Product
from .models import WishlistItem


class WishlistAPITests(TestCase):
    def test_add_idempotently_and_delete(self):
        user = get_user_model().objects.create_user(name="Buyer", mobile="9876543210", email="buyer@example.com")
        category = Category.objects.create(name="Books", slug="books")
        product = Product.objects.create(name="Guide", slug="guide", sku="G1", category=category, price="100.00", stock=1)
        client = APIClient()
        self.assertIn(client.get("/api/wishlist/").status_code, (401, 403))
        client.force_authenticate(user)
        self.assertEqual(client.post("/api/wishlist/", {"product_id": product.pk}).status_code, 201)
        self.assertEqual(client.post("/api/wishlist/", {"product_id": product.pk}).status_code, 200)
        self.assertEqual(WishlistItem.objects.count(), 1)
        self.assertEqual(client.delete(f"/api/wishlist/items/{WishlistItem.objects.get().pk}/").status_code, 204)
