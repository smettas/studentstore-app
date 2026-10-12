from rest_framework import serializers
from .models import Brand, Category, Product, ProductImage, StudyLevel


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "parent")


class StudyLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyLevel
        fields = ("id", "name", "slug")


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ("id", "name", "slug")


class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ("id", "image_url", "alt_text", "position")

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    study_levels = StudyLevelSerializer(many=True, read_only=True)
    primary_image = serializers.SerializerMethodField()
    effective_price = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ("id", "name", "slug", "sku", "category", "brand", "study_levels",
                  "product_type", "price", "discount_price", "effective_price", "stock",
                  "in_stock", "primary_image")

    def get_primary_image(self, obj):
        image = next(iter(obj.images.all()), None)
        return ProductImageSerializer(image, context=self.context).data if image else None

    def get_effective_price(self, obj):
        return str(obj.discount_price if obj.discount_price is not None else obj.price)

    def get_in_stock(self, obj):
        return obj.stock > 0


class ProductDetailSerializer(ProductListSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ("description", "images", "created_at", "updated_at")
