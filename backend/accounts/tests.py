from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from accounts.models import OTPChallenge
from accounts.services.otp_service import _digest


@override_settings(OTP_PROVIDER="console")
class AccountsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.mobile = "9876543210"

    @patch("accounts.services.otp_service.send_otp_sms")
    def test_signup_verify_profile_refresh(self, sms):
        response = self.client.post(reverse("signup"), {
            "name": "Student", "mobile": self.mobile, "email": "student@example.com"
        }, format="json")
        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(mobile=self.mobile)
        self.assertFalse(user.is_active)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(sms.call_count, 1)
        challenge = OTPChallenge.objects.get(mobile=self.mobile)
        challenge.code_hash = _digest(self.mobile, "123456")
        challenge.save(update_fields=["code_hash"])
        response = self.client.post(reverse("otp-verify"), {"mobile": self.mobile, "otp": "123456"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + response.data["access"])
        self.assertEqual(self.client.get(reverse("profile")).status_code, 200)
        self.assertTrue(get_user_model().objects.get(mobile=self.mobile).is_active)
        self.assertEqual(self.client.post(reverse("otp-verify"), {"mobile": self.mobile, "otp": "123456"}).status_code, 400)

    @patch("accounts.services.otp_service.send_otp_sms")
    def test_unknown_mobile_has_generic_response(self, sms):
        response = self.client.post(reverse("otp-send"), {"mobile": self.mobile}, format="json")
        self.assertEqual(response.status_code, 200)
        sms.assert_not_called()

    def test_invalid_signup(self):
        response = self.client.post(reverse("signup"), {"name": "X", "mobile": "123", "email": "bad"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_profile_requires_jwt(self):
        self.assertEqual(self.client.get(reverse("profile")).status_code, 401)

    @patch("accounts.services.otp_service.send_otp_sms", side_effect=RuntimeError("provider down"))
    def test_failed_sms_invalidates_challenge(self, sms):
        response = self.client.post(reverse("signup"), {"name": "Student", "mobile": self.mobile, "email": "student@example.com"}, format="json")
        self.assertEqual(response.status_code, 400)
        challenge = OTPChallenge.objects.get(mobile=self.mobile)
        self.assertLessEqual(challenge.expires_at, challenge.created_at + __import__("datetime").timedelta(seconds=1))
