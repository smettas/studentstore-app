from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from .models import Notification, PushDevice
from .services.expo_push import send_notification


class NotificationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(name="Test User", mobile="9876543210", email="test@example.com")
        self.other = User.objects.create_user(name="Other User", mobile="9876543211", email="other@example.com")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_authentication_required(self):
        self.assertIn(APIClient().get(reverse("notification-list")).status_code, (401, 403))

    def test_notification_isolation_and_read(self):
        mine = Notification.objects.create(user=self.user, title="Mine", body="Message")
        other = Notification.objects.create(user=self.other, title="Other", body="Secret")
        response = self.client.get(reverse("notification-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(self.client.post(reverse("notification-read", args=[other.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("notification-read", args=[mine.pk])).status_code, 200)
        mine.refresh_from_db()
        self.assertTrue(mine.is_read)

    def test_device_registration_reassignment_and_unregister(self):
        token = "ExponentPushToken[abc_123]"
        response = self.client.post(reverse("push-device-register"), {"expo_push_token": token})
        self.assertEqual(response.status_code, 201)
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.post(reverse("push-device-register"), {"expo_push_token": token}).status_code, 200)
        self.assertEqual(PushDevice.objects.get(expo_push_token=token).user, self.other)
        self.client.force_authenticate(user=self.user)
        self.assertFalse(self.client.post(reverse("push-device-unregister"), {"expo_push_token": token}).data["unregistered"])
        self.client.force_authenticate(user=self.other)
        self.assertTrue(self.client.post(reverse("push-device-unregister"), {"expo_push_token": token}).data["unregistered"])

    @patch("notifications.services.expo_push.requests.post")
    def test_push_sender(self, mock_post):
        PushDevice.objects.create(user=self.user, expo_push_token="ExpoPushToken[abc]")
        notification = Notification.objects.create(user=self.user, title="Test", body="Hello")
        mock_post.return_value.json.return_value = {"data": [{"status": "ok", "id": "ticket"}]}
        self.assertEqual(len(send_notification(notification)), 1)
        mock_post.assert_called_once()
