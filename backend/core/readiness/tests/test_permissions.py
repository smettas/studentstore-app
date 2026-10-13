"""Smoke tests for anonymous access to protected API endpoints."""
from django.test import SimpleTestCase


class AnonymousPermissionTests(SimpleTestCase):
    def test_private_endpoints_reject_anonymous_requests(self):
        for url in (
            '/api/accounts/profile/',
            '/api/cart/',
            '/api/wishlist/',
            '/api/addresses/',
            '/api/orders/',
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn(response.status_code, (401, 403))
