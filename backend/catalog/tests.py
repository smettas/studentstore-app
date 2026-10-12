from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from .models import Brand, Category, Product, ProductImage, StudyLevel


class CatalogAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Books", slug="books")
        cls.brand = Brand.objects.create(name="Acme", slug="acme")
        cls.neet = StudyLevel.objects.create(name="NEET", slug="neet")
        cls.jee = StudyLevel.objects.create(name="JEE", slug="jee")
        cls.product = Product.objects.create(
            name="Exam Guide", slug="exam-guide", sku="GUIDE-1", category=cls.category,
            brand=cls.brand, price=Decimal("200.00"), discount_price=Decimal("150.00"), stock=3)
        cls.product.study_levels.add(cls.neet, cls.jee)
        cls.other = Product.objects.create(
            name="Pen", slug="pen", sku="PEN-1", category=cls.category,
            price=Decimal("20.00"), stock=0)
        Product.objects.create(name="Hidden", slug="hidden", sku="HIDDEN-1",
                               category=cls.category, price=Decimal("10.00"), is_active=False)

    def test_product_can_have_multiple_study_levels(self):
        self.assertEqual(self.product.study_levels.count(), 2)

    def test_public_listing_and_hidden_products(self):
        response = self.client.get(reverse("catalog-products"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 2)

    def test_study_level_filter_does_not_restrict_other_levels(self):
        for level in ("neet", "jee"):
            response = self.client.get(reverse("catalog-products"), {"study_level": level})
            self.assertEqual(response.json()["count"], 1)
            self.assertEqual(response.json()["results"][0]["sku"], "GUIDE-1")

    def test_search_and_selling_price_filter(self):
        response = self.client.get(reverse("catalog-products"),
                                   {"search": "guide", "min_price": "140", "max_price": "160"})
        self.assertEqual(response.json()["count"], 1)

    def test_bad_price_returns_400(self):
        self.assertEqual(self.client.get(reverse("catalog-products"), {"min_price": "oops"}).status_code, 400)

    def test_product_detail_and_images(self):
        response = self.client.get(reverse("catalog-product-detail", args=["exam-guide"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["effective_price"], "150.00")
        self.assertEqual(response.json()["images"], [])

    def test_inactive_product_not_visible(self):
        self.assertEqual(self.client.get(reverse("catalog-product-detail", args=["hidden"])).status_code, 404)

    def test_reference_endpoints(self):
        for name in ("catalog-categories", "catalog-brands", "catalog-study-levels"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_stock_filter(self):
        response = self.client.get(reverse("catalog-products"), {"in_stock": "true"})
        self.assertEqual(response.json()["count"], 1)
