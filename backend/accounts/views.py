from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.serializers import MobileSerializer, ProfileSerializer, SignupSerializer, VerifyOTPSerializer
from accounts.services.otp_service import consume_otp, issue_otp


class OTPRequestThrottle(AnonRateThrottle):
    scope = "otp_request"


class OTPVerifyThrottle(AnonRateThrottle):
    scope = "otp_verify"


class SignupView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPRequestThrottle]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        User = get_user_model()
        if User.objects.filter(mobile=data["mobile"]).exists():
            return Response({"detail": "Mobile number is already registered."}, status=400)
        if User.objects.filter(email__iexact=data["email"]).exists():
            return Response({"detail": "Email is already registered."}, status=400)
        try:
            with transaction.atomic():
                user = User.objects.create_user(**data, is_active=False)
        except IntegrityError:
            return Response({"detail": "Account already exists."}, status=400)
        # Signup sends OTP; verification activates the user.
        issue_otp(user.mobile)
        return Response({"detail": "Signup received. Verify the OTP to activate your account.", "mobile": user.mobile}, status=status.HTTP_201_CREATED)


class SendOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPRequestThrottle]

    def post(self, request):
        serializer = MobileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mobile = serializer.validated_data["mobile"]
        if get_user_model().objects.filter(mobile=mobile, is_active=True).exists():
            issue_otp(mobile)
        # Identical response for unknown mobile numbers to reduce enumeration.
        return Response({"detail": "If the mobile number is registered, an OTP has been sent."})


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPVerifyThrottle]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mobile = serializer.validated_data["mobile"]
        user = get_user_model().objects.filter(mobile=mobile).first()
        if user is None:
            return Response({"otp": "Invalid or expired OTP."}, status=400)
        consume_otp(mobile, serializer.validated_data["otp"])
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])
        refresh = RefreshToken.for_user(user)
        return Response({"access": str(refresh.access_token), "refresh": str(refresh), "user": ProfileSerializer(user).data})


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(ProfileSerializer(request.user).data)
