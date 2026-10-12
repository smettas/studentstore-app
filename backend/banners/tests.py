from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from .models import Banner


class BannerTests(TestCase):
    def test_public_list_excludes_inactive_and_expired(self):
        now = timezone.now()
        Banner.objects.create(title="Live", image="banners/live.png", position=1)
        Banner.objects.create(title="Expired", image="banners/old.png", expires_at=now-timedelta(seconds=1))
        Banner.objects.create(title="Future", image="banners/new.png", starts_at=now+timedelta(days=1))
        Banner.objects.create(title="Disabled", image="banners/off.png", is_active=False)
        response = APIClient().get(reverse("banner-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([b["title"] for b in response.data], ["Live"])
