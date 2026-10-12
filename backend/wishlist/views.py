from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import WishlistItem
from .serializers import WishlistAddSerializer, WishlistItemSerializer


class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = WishlistItem.objects.filter(user=request.user).select_related("product", "product__category", "product__brand").prefetch_related("product__study_levels", "product__images").order_by("-created_at")
        return Response(WishlistItemSerializer(items, many=True, context={"request": request}).data)

    def post(self, request):
        serializer = WishlistAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item, created = WishlistItem.objects.get_or_create(user=request.user, product=serializer.validated_data["product"])
        return Response(WishlistItemSerializer(item, context={"request": request}).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class WishlistItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        item = get_object_or_404(WishlistItem, pk=item_id, user=request.user)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
