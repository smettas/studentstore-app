from decimal import Decimal
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Cart, CartItem
from .serializers import CartItemSerializer, CartItemWriteSerializer, QuantitySerializer


def cart_response(cart, request):
    items = list(cart.items.select_related("product", "product__category", "product__brand").prefetch_related("product__study_levels", "product__images"))
    total = sum((item.quantity * (item.product.discount_price if item.product.discount_price is not None else item.product.price) for item in items), Decimal("0.00"))
    return Response({"items": CartItemSerializer(items, many=True, context={"request": request}).data, "total": str(total), "item_count": sum(i.quantity for i in items)})


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart_response(cart, request)

    def delete(self, request):
        CartItem.objects.filter(cart__user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CartItemWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data["quantity"]
        with transaction.atomic():
            cart, _ = Cart.objects.get_or_create(user=request.user)
            item, _ = CartItem.objects.select_for_update().get_or_create(cart=cart, product=product, defaults={"quantity": 0})
            new_quantity = item.quantity + quantity
            if new_quantity > 100 or new_quantity > product.stock:
                return Response({"quantity": ["Requested quantity exceeds available stock or cart limit."]}, status=400)
            item.quantity = new_quantity
            item.save(update_fields=["quantity"])
        return Response(CartItemSerializer(item, context={"request": request}).data, status=status.HTTP_200_OK)


class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        serializer = QuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            item = get_object_or_404(CartItem.objects.select_for_update().select_related("product"), pk=item_id, cart__user=request.user)
            quantity = serializer.validated_data["quantity"]
            if not item.product.is_active or quantity > item.product.stock:
                return Response({"quantity": ["Product unavailable or insufficient stock."]}, status=400)
            item.quantity = quantity
            item.save(update_fields=["quantity"])
        return Response(CartItemSerializer(item, context={"request": request}).data)

    def delete(self, request, item_id):
        item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
