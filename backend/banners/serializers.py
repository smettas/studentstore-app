from rest_framework import serializers
from .models import Banner


class BannerSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Banner
        fields = ("id", "title", "image", "target_url", "position", "starts_at", "expires_at")
