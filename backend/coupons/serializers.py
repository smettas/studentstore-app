from rest_framework import serializers


class CouponValidationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=40, trim_whitespace=True)
