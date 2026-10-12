from rest_framework import serializers

class RazorpayStartSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)

class RazorpayVerifySerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
    razorpay_order_id = serializers.CharField(max_length=120)
    razorpay_payment_id = serializers.CharField(max_length=120)
    razorpay_signature = serializers.CharField(max_length=255)

class CODConfirmSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
