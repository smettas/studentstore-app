"""Regression tests for precise catalogue search shared by website and app.

Run: python manage.py test catalog.test_search_relevance --settings=config.settings.local
These tests create an isolated test database; they do not modify production data.
"""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Brand, Category, Product


class PreciseProductSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Office stationery", slug="office-stationery")
        cls.branded = Brand.objects.create(name="Camel", slug="camel")
        items = [
            ("Ballpoint Pen - Pack of 10", "pen-10", "PEN-10", "Writes smoothly"),
            ("Gel Pens - Pack of 5", "pens-5", "PENS-5", "Blue ink pens"),
            ("Colour Pencil Set", "pencils", "PENCIL-5", "For use with a pen"),
            ("A4 Colour Paper", "paper", "PAPER-3", "Perfect for pen and pencil work"),
            ("Stapler - Single piece", "stapler", "STAPLER-1", "Small desk stapler"),
            ("Staple Pins - Pack of 3", "staple-pins", "STAPLE-3", "Replacement for staplers"),
            ("Exam Register", "register", "REGISTER-4", "Works with a pen or stapler"),
        ]
        for name, slug, sku, description in items:
            Product.objects.create(
                name=name, slug=slug, sku=sku, category=cls.category,
                brand=cls.branded if sku == "PAPER-3" else None,
                description=description, price=Decimal("100"), stock=12,
            )

    def search(self, phrase):
        response = self.client.get(reverse("catalog-products"), {"search": phrase})
        self.assertEqual(response.status_code, 200, response.content)
        return {p["sku"] for p in response.json()["results"]}

    def test_pen_does_not_match_pencils_paper_register(self):
        self.assertEqual(self.search("pen"), {"PEN-10", "PENS-5"})

    def test_stapler_does_not_match_staple_pins(self):
        self.assertEqual(self.search("stapler"), {"STAPLER-1"})

    def test_common_stapler_typo_is_corrected(self):
        self.assertEqual(self.search("staler"), {"STAPLER-1"})

    def test_pencil_does_not_match_pen(self):
        self.assertEqual(self.search("pencil"), {"PENCIL-5"})

    def test_only_explicit_brand_search_returns_brand_items(self):
        self.assertEqual(self.search("Camel"), {"PAPER-3"})

    def test_unknown_product_does_not_match_descriptions(self):
        self.assertEqual(self.search("fictional"), set())

    def test_pen_search_and_brand_filter_remain_composable(self):
        response = self.client.get(reverse("catalog-products"), {"search": "pen", "brand": "camel"})
        self.assertEqual(response.json()["count"], 0)
