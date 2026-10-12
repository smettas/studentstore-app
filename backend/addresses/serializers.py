import re
from rest_framework import serializers
from .models import Address


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ("id", "recipient_name", "phone", "line1", "line2", "landmark", "city", "state", "postal_code", "is_default", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_phone(self, value):
        if not re.fullmatch(r"[6-9]\d{9}", value):
            raise serializers.ValidationError("Enter a valid 10-digit Indian mobile number.")
        return value

    def validate_postal_code(self, value):
        if not re.fullmatch(r"[1-9]\d{5}", value):
            raise serializers.ValidationError("Enter a valid 6-digit Indian PIN code.")
        return value
