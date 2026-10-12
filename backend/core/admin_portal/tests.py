from django.test import SimpleTestCase, override_settings
from django.urls import resolve, reverse

class PortalRoutesTests(SimpleTestCase):
    def test_all_pages_have_distinct_routes(self):
        names = ("dashboard", "products", "categories", "stock", "orders", "coupons", "banners", "reports")
        paths = [reverse(f"staff_portal:{name}") for name in names]
        self.assertEqual(len(set(paths)), 8)
        for path in paths:
            self.assertTrue(callable(resolve(path).func))

    def test_anonymous_redirected_to_admin_login(self):
        for name in ("dashboard", "products", "categories", "stock", "orders", "coupons", "banners", "reports"):
            response = self.client.get(reverse(f"staff_portal:{name}"))
            self.assertEqual(response.status_code, 302)
            self.assertIn("/admin/login/", response["Location"])
