from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from orders.models import OrderItem, Order
from .models import Product, ProductReview


class ReviewInputSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    title = serializers.CharField(max_length=120, required=False, allow_blank=True)
    comment = serializers.CharField(max_length=2000, allow_blank=False, trim_whitespace=True)


def review_payload(review):
    return {"id": review.id, "rating": review.rating, "title": review.title,
            "comment": review.comment, "created_at": review.created_at,
            "verified_purchase": True, "customer": "Verified customer"}


class ProductReviewView(APIView):
    def get_permissions(self):
        return [AllowAny()] if self.request.method == "GET" else [IsAuthenticated()]

    def get_product(self, slug):
        return get_object_or_404(Product, slug=slug, is_active=True)

    def get(self, request, slug):
        product = self.get_product(slug)
        qs = ProductReview.objects.filter(product=product, is_approved=True)
        stats = qs.aggregate(average=Avg("rating"), count=Count("id"))
        reviews = qs.order_by("-created_at")[:30]
        return Response({"average_rating": round(stats["average"], 1) if stats["average"] is not None else None,
                         "review_count": stats["count"], "results": [review_payload(r) for r in reviews]})

    def post(self, request, slug):
        product = self.get_product(slug)
        # Only purchasers with a delivered order may submit a review.
        purchased = OrderItem.objects.filter(product=product, order__user=request.user,
                                            order__status=Order.Status.DELIVERED).exists()
        if not purchased:
            return Response({"detail": "Reviews are available after your order is delivered."}, status=403)
        serializer = ReviewInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review, created = ProductReview.objects.update_or_create(
            product=product, user=request.user,
            defaults={**serializer.validated_data, "is_approved": False})
        return Response({"detail": "Review submitted for moderation.", "id": review.id},
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
