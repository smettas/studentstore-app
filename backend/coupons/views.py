from decimal import Decimal
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import CouponValidationSerializer
from .services import validate_coupon


class CouponValidateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CouponValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from cart.models import CartItem
        items = CartItem.objects.filter(cart__user=request.user).select_related("product")
        subtotal = Decimal("0.00")
        for item in items:
            product = item.product
            if not product.is_active or item.quantity > product.stock:
                return Response({"detail": "Cart contains unavailable products or insufficient stock."}, status=400)
            subtotal += item.quantity * (product.discount_price if product.discount_price is not None else product.price)
        if not items.exists():
            return Response({"detail": "Cart is empty."}, status=400)
        coupon, discount = validate_coupon(serializer.validated_data["code"], subtotal)
        return Response({"code": coupon.code, "subtotal": str(subtotal), "discount": str(discount), "total_after_discount": str(subtotal - discount)})
