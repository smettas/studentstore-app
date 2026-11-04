from django.urls import path
from .views import (BrandListView, CategoryListView, ProductDetailView,
                    ProductListView, StudyLevelListView)

from .review_views import ProductReviewView

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="catalog-categories"),
    path("study-levels/", StudyLevelListView.as_view(), name="catalog-study-levels"),
    path("brands/", BrandListView.as_view(), name="catalog-brands"),
    path("products/", ProductListView.as_view(), name="catalog-products"),
    path("products/<slug:slug>/reviews/", ProductReviewView.as_view(), name="catalog-product-reviews"),
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="catalog-product-detail"),
]
