from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from .serializers import CODConfirmSerializer, RazorpayStartSerializer, RazorpayVerifySerializer
from .services.payment_service import confirm_cod, start_razorpay, verify_razorpay
from .services.webhook_service import process_webhook


class RazorpayStartView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = RazorpayStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(start_razorpay(request.user, serializer.validated_data["order_id"]))


class RazorpayVerifyView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = RazorpayVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = verify_razorpay(request.user, serializer.validated_data)
        return Response({"order_id": payment.order_id, "payment_status": payment.status})


class CODConfirmView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = CODConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = confirm_cod(request.user, serializer.validated_data["order_id"])
        return Response({"order_id": payment.order_id, "payment_status": payment.status,
                         "order_status": payment.order.status})


@csrf_exempt
def razorpay_webhook(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed."}, status=405)
    try:
        result = process_webhook(request.body, request.headers.get("X-Razorpay-Signature", ""))
    except ValidationError as exc:
        return JsonResponse({"detail": exc.detail}, status=400)
    except Exception:
        # Allow Razorpay to retry transient failures; do not expose internal details.
        return JsonResponse({"detail": "Processing failed; retry later."}, status=500)
    return JsonResponse({"result": result})
