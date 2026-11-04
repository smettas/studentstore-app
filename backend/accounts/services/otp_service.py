"""OTP generation, storage, and verification. Never store plaintext OTPs."""
import hashlib
import hmac
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import Throttled, ValidationError

from accounts.models import OTPChallenge
from accounts.services.sms_service import send_otp_sms

logger = logging.getLogger(__name__)
OTP_LIFETIME_SECONDS = 300
OTP_COOLDOWN_SECONDS = 60
OTP_MAX_ATTEMPTS = 5


def _digest(mobile, code):
    key = settings.SECRET_KEY.encode("utf-8")
    return hmac.new(key, f"{mobile}:{code}".encode("utf-8"), hashlib.sha256).hexdigest()


def issue_otp(mobile, *, return_code=False):
    now = timezone.now()
    with transaction.atomic():
        latest = OTPChallenge.objects.select_for_update().filter(mobile=mobile).order_by("-created_at", "-pk").first()
        if latest and (now - latest.created_at).total_seconds() < OTP_COOLDOWN_SECONDS:
            raise Throttled(detail="Please wait before requesting another OTP.")
        code = f"{secrets.randbelow(1000000):06d}"
        challenge = OTPChallenge.objects.create(
            mobile=mobile, code_hash=_digest(mobile, code),
            expires_at=now + timedelta(seconds=OTP_LIFETIME_SECONDS),
        )
    try:
        send_otp_sms(mobile, code)
    except Exception:
        # Invalidate undelivered OTP. Do not reveal provider details to callers.
        OTPChallenge.objects.filter(pk=challenge.pk).update(expires_at=timezone.now())
        logger.exception("OTP SMS delivery failed")
        raise ValidationError({"detail": "Could not send OTP. Please try again later."})
    return code if return_code else OTP_LIFETIME_SECONDS


def consume_otp(mobile, code):
    with transaction.atomic():
        challenge = OTPChallenge.objects.select_for_update().filter(mobile=mobile).order_by("-created_at", "-pk").first()
        if challenge is None or challenge.verified_at or challenge.expires_at <= timezone.now():
            raise ValidationError({"otp": "Invalid or expired OTP."})
        if challenge.attempts >= OTP_MAX_ATTEMPTS:
            raise ValidationError({"otp": "Too many attempts. Request a new OTP."})
        # Use an atomic F update to persist attempts even when verification fails.
        OTPChallenge.objects.filter(pk=challenge.pk).update(attempts=challenge.attempts + 1)
        if not hmac.compare_digest(challenge.code_hash, _digest(mobile, code)):
            raise ValidationError({"otp": "Invalid or expired OTP."})
        OTPChallenge.objects.filter(pk=challenge.pk).update(verified_at=timezone.now())
