from django.core.management.base import BaseCommand
from django.db import transaction
from delivery.models import DeliveryPincode, DeliverySettings

class Command(BaseCommand):
    help = "Set estimated delivery to 1–2 business days for enabled Bengaluru PINs; preserve disabled coverage and COD flags."

    def handle(self, *args, **options):
        with transaction.atomic():
            count = DeliveryPincode.objects.filter(is_serviceable=True).update(min_days=1, max_days=2)
            settings_count = DeliverySettings.objects.update(estimated_min_days=1, estimated_max_days=2)
        self.stdout.write(self.style.SUCCESS(f"Updated {count} serviceable PINs and {settings_count} delivery settings records to 1–2 days. Existing disabled PINs and COD flags unchanged."))
