from decimal import Decimal
from rest_framework import serializers
from catalog.models import Product
from catalog.serializers import ProductListSerializer
from .models import CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    unit_price = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ("id", "product", "quantity", "unit_price", "line_total")

    def get_unit_price(self, obj):
        p = obj.product
        return str(p.discount_price if p.discount_price is not None else p.price)

    def get_line_total(self, obj):
        return str(Decimal(self.get_unit_price(obj)) * obj.quantity)


class CartItemWriteSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True), source="product")
    quantity = serializers.IntegerField(min_value=1, max_value=100)

    def validate(self, attrs):
        product = attrs["product"]
        if product.stock < attrs["quantity"]:
            raise serializers.ValidationError({"quantity": "Insufficient stock."})
        return attrs


class QuantitySerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, max_value=100)
