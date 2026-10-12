from django.contrib.auth import get_user_model
from rest_framework import serializers
import re

MOBILE_PATTERN = re.compile(r"^[6-9][0-9]{9}$")


def validate_mobile(value):
    if not MOBILE_PATTERN.fullmatch(value):
        raise serializers.ValidationError("Enter a valid 10-digit Indian mobile number.")
    return value


class SignupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, trim_whitespace=True)
    mobile = serializers.CharField(validators=[validate_mobile])
    email = serializers.EmailField(max_length=254)

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name is required.")
        return value.strip()

    def validate_email(self, value):
        return value.strip().lower()


class MobileSerializer(serializers.Serializer):
    mobile = serializers.CharField(validators=[validate_mobile])


class VerifyOTPSerializer(MobileSerializer):
    otp = serializers.RegexField(regex=r"^[0-9]{6}$", max_length=6)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "name", "mobile", "email", "date_joined")
        read_only_fields = fields
