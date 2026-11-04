from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory


class CheckoutSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(min_value=1)
    coupon_code = serializers.CharField(max_length=40, required=False, allow_blank=True)
    payment_method = serializers.ChoiceField(choices=["cod"])


class OrderItemSerializer(serializers.ModelSerializer):
    product_slug = serializers.CharField(source="product.slug", read_only=True, default=None)
    image_url = serializers.SerializerMethodField()

    def get_image_url(self, obj):
        image = obj.product.images.order_by("position", "id").first() if obj.product_id else None
        if not image or not image.image:
            return None
        url = image.image.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url
    class Meta:
        model = OrderItem
        fields = ("id", "product", "product_slug", "image_url", "product_name", "sku", "quantity", "unit_price", "line_total")


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ("status", "note", "created_at")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    coupon_code = serializers.CharField(source="coupon.code", read_only=True, default=None)
    payment_method = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ("id", "status", "shipping_name", "shipping_phone", "shipping_address", "subtotal", "discount_total", "shipping_fee", "total", "coupon_code", "payment_method", "items", "status_history", "created_at", "updated_at")

    def get_payment_method(self, obj):
        payment = next(iter(obj.payments.all()), None)
        return payment.method if payment else None
