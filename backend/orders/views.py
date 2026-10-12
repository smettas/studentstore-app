from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Order
from .serializers import CheckoutSerializer, OrderSerializer
from .services import cancel_order, create_order


def orders_for_user(user):
    return Order.objects.filter(user=user).select_related("coupon").prefetch_related("items", "status_history", "payments").order_by("-created_at")


class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(OrderSerializer(orders_for_user(request.user), many=True).data)

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = create_order(user=request.user, **serializer.validated_data)
        order = get_object_or_404(orders_for_user(request.user), pk=order.pk)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(orders_for_user(request.user), pk=order_id)
        return Response(OrderSerializer(order).data)


class OrderCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        if not Order.objects.filter(pk=order_id, user=request.user).exists():
            return Response({"detail": "Not found."}, status=404)
        order = cancel_order(order_id=order_id, user=request.user)
        return Response(OrderSerializer(get_object_or_404(orders_for_user(request.user), pk=order.pk)).data)
