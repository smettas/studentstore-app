from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.views import ProfileView, SendOTPView, SignupView, VerifyOTPView

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("otp/send/", SendOTPView.as_view(), name="otp-send"),
    path("otp/verify/", VerifyOTPView.as_view(), name="otp-verify"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("profile/", ProfileView.as_view(), name="profile"),
]
