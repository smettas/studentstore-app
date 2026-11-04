"""Print selected Django DB identity and optionally verify private R2 connectivity."""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from catalog.batch02.guards import EXPECTED_BUCKET, db_identity
from catalog.models import Product, ProductImage
from catalog.batch02.storage_ops import make_r2_client

class Command(BaseCommand):
    help = "Print NONSECRET database identity/product counts and check isolated R2 bucket."

    def add_arguments(self, parser):
        parser.add_argument("--check-r2", action="store_true")

    def handle(self, *args, **options):
        try:
            connection.ensure_connection()
            identity = db_identity()
            for key, value in identity.items():
                self.stdout.write(f"{key}: {value}")
            self.stdout.write(f"settings_module: {settings.SETTINGS_MODULE}")
            self.stdout.write(f"media_provider: {settings.STUDENTSTORE_MEDIA_PROVIDER}")
            self.stdout.write(f"r2_delivery_mode: {getattr(settings, 'R2_DELIVERY_MODE', 'proxy')}")
            self.stdout.write(f"products: {Product.objects.count()}")
            self.stdout.write(f"active_products: {Product.objects.filter(is_active=True).count()}")
            self.stdout.write(f"image_records: {ProductImage.objects.count()}")
            self.stdout.write(f"batch02_products: {Product.objects.filter(sku__startswith='OJAS-B02-').count()}")
            if options['check_r2']:
                client, bucket = make_r2_client()
                if bucket != EXPECTED_BUCKET:
                    raise CommandError("Configured bucket is not ojasone-studentstore.")
                client.head_bucket(Bucket=bucket)
                self.stdout.write(self.style.SUCCESS("R2 head_bucket: OK (private S3 API)"))
        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(f"Connectivity check failed ({type(exc).__name__}); inspect settings privately.") from None
