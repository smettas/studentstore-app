from django.urls import path
from .views import CODConfirmView, RazorpayStartView, RazorpayVerifyView, razorpay_webhook

urlpatterns = [
    path("razorpay/create/", RazorpayStartView.as_view(), name="razorpay-create"),
    path("razorpay/verify/", RazorpayVerifyView.as_view(), name="razorpay-verify"),
    path("razorpay/webhook/", razorpay_webhook, name="razorpay-webhook"),
    path("cod/confirm/", CODConfirmView.as_view(), name="cod-confirm"),
]
