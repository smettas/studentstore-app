"""SMS adapter. Console OTP is permitted only in DEBUG mode."""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_otp_sms(mobile, code):
    provider = getattr(settings, "OTP_PROVIDER", "console")
    if provider == "console":
        if not settings.DEBUG:
            raise RuntimeError("Console OTP is forbidden outside DEBUG mode")
        logger.warning("DEVELOPMENT ONLY — OTP for %s: %s", mobile, code)
        return
    if provider == "msg91":
        import json
        import urllib.request
        import urllib.error
        authkey = getattr(settings, "MSG91_AUTH_KEY", "")
        template_id = getattr(settings, "MSG91_TEMPLATE_ID", "")
        if not authkey or not template_id:
            raise RuntimeError("MSG91 credentials/template not configured")
        # MSG91 Flow template must have the variable OTP configured.
        payload = json.dumps({
            "template_id": template_id,
            "short_url": "0",
            "recipients": [{"mobiles": "91" + mobile, "OTP": code}],
        }).encode("utf-8")
        request = urllib.request.Request(
            "https://control.msg91.com/api/v5/flow/",
            data=payload,
            headers={"authkey": authkey, "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            if response.status >= 300 or result.get("type") != "success":
                raise RuntimeError("MSG91 rejected the SMS request")
        return
    raise RuntimeError("Unknown OTP_PROVIDER")
