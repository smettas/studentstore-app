from rest_framework import serializers
from .models import Notification, PushDevice


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id", "title", "body", "data", "is_read", "created_at")
        read_only_fields = fields


class PushDeviceSerializer(serializers.Serializer):
    expo_push_token = serializers.RegexField(
        regex=r"^(Expo(nent)?PushToken)\[[A-Za-z0-9_-]+\]$",
        max_length=255,
        help_text="ExpoPushToken[...] or ExponentPushToken[...]",
    )


class DeviceUnregisterSerializer(PushDeviceSerializer):
    pass
