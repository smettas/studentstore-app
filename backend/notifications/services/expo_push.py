"""Explicit push sender; no network traffic occurs during Django imports."""
import logging
import requests
from django.conf import settings
from notifications.models import PushDevice

logger = logging.getLogger(__name__)
EXPO_ENDPOINT = "https://exp.host/--/api/v2/push/send"


def send_notification(notification):
    """Send a stored notification; returns provider tickets (not delivery receipts).

    Call from a trusted job/admin action, not from public user input. Production
    should use a background queue and process Expo receipts/retries.
    """
    tokens = list(PushDevice.objects.filter(user=notification.user, is_active=True)
                  .values_list("expo_push_token", flat=True))
    if not tokens:
        return []
    messages = [{
        "to": token, "title": notification.title, "body": notification.body,
        "data": notification.data or {}, "sound": "default",
    } for token in tokens]
    tickets = []
    # Expo supports batches up to 100 notifications.
    for index in range(0, len(messages), 100):
        batch = messages[index:index + 100]
        try:
            response = requests.post(
                EXPO_ENDPOINT,
                json=batch,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            result = payload.get("data", [])
            if isinstance(result, dict):
                result = [result]
            if not isinstance(result, list):
                logger.warning("Unexpected Expo response format")
                continue
            tickets.extend(result)
            for message, ticket in zip(batch, result):
                if ticket.get("status") == "error" and ticket.get("details", {}).get("error") == "DeviceNotRegistered":
                    PushDevice.objects.filter(expo_push_token=message["to"]).update(is_active=False)
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Expo push request failed: %s", exc)
    return tickets
