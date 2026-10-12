from rest_framework import generics
from rest_framework.permissions import AllowAny
from .filters import filter_products
from .pagination import CatalogPagination
from .models import Brand, Category, Product, StudyLevel
from .serializers import (BrandSerializer, CategorySerializer, ProductDetailSerializer,
                          ProductListSerializer, StudyLevelSerializer)


class PublicCatalogMixin:
    permission_classes = (AllowAny,)
    authentication_classes = ()


class CategoryListView(PublicCatalogMixin, generics.ListAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.filter(is_active=True).order_by("name")
    pagination_class = None


class StudyLevelListView(PublicCatalogMixin, generics.ListAPIView):
    serializer_class = StudyLevelSerializer
    queryset = StudyLevel.objects.all().order_by("name")
    pagination_class = None


class BrandListView(PublicCatalogMixin, generics.ListAPIView):
    serializer_class = BrandSerializer
    queryset = Brand.objects.all().order_by("name")
    pagination_class = None


class ProductListView(PublicCatalogMixin, generics.ListAPIView):
    serializer_class = ProductListSerializer
    pagination_class = CatalogPagination

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True, category__is_active=True)
        qs = filter_products(qs, self.request.query_params)
        ordering = self.request.query_params.get("ordering", "newest")
        if ordering not in ("newest", "price_asc", "price_desc", "name"):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"ordering": "Use newest, price_asc, price_desc, or name."})
        if ordering.startswith("price_"):
            from django.db.models.functions import Coalesce
            qs = qs.annotate(selling_price=Coalesce("discount_price", "price"))
        sort_fields = {"newest": ("-created_at", "-id"), "price_asc": ("selling_price", "id"),
                       "price_desc": ("-selling_price", "id"), "name": ("name", "id")}
        return qs.select_related("category", "brand").prefetch_related("study_levels", "images").order_by(*sort_fields[ordering])


class ProductDetailView(PublicCatalogMixin, generics.RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    lookup_field = "slug"
    queryset = (Product.objects.filter(is_active=True, category__is_active=True)
                .select_related("category", "brand").prefetch_related("study_levels", "images"))
