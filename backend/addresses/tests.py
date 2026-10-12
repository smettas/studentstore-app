from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Address


class AddressAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(name="Buyer", mobile="9876543210", email="buyer@example.com")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.payload = {"recipient_name": "Buyer", "phone": "9876543210", "line1": "Main Road", "city": "Bengaluru", "state": "Karnataka", "postal_code": "560001"}

    def test_default_switch_and_owner_isolation(self):
        first = self.client.post("/api/addresses/", self.payload)
        self.assertEqual(first.status_code, 201)
        self.assertTrue(Address.objects.get(pk=first.data["id"]).is_default)
        second = self.client.post("/api/addresses/", {**self.payload, "line1": "Second Road", "is_default": True})
        self.assertEqual(second.status_code, 201)
        self.assertEqual(Address.objects.filter(user=self.user, is_default=True).count(), 1)
        self.assertEqual(self.client.post(f'/api/addresses/{first.data["id"]}/default/').status_code, 200)
        other = get_user_model().objects.create_user(name="Other", mobile="9876543211", email="other@example.com")
        self.client.force_authenticate(other)
        self.assertEqual(self.client.get(f'/api/addresses/{first.data["id"]}/').status_code, 404)

    def test_pin_validation(self):
        self.assertEqual(self.client.post("/api/addresses/", {**self.payload, "postal_code": "123"}).status_code, 400)
