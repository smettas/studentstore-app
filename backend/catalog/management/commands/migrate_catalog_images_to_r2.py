"""Stage and migrate existing local product photos to durable Cloudflare R2."""
import csv
import json
import mimetypes
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from catalog.batch02.sources import ImageSource, MAX_IMAGE_BYTES
from catalog.batch02.storage_ops import make_r2_client, put_r2_verified
from catalog.batch02.guards import verify_production, EXPECTED_BUCKET
from catalog.models import ProductImage


class Command(BaseCommand):
    help = 'Verify and stage local product images to R2; update DB image paths only with R2 as default.'

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument('--dry-run', action='store_true')
        mode.add_argument('--commit', action='store_true')
        parser.add_argument('--images', help='Optional numbered image ZIP/folder fallback for batch-02')
        parser.add_argument('--batch-only', action='store_true', help='Migrate only OJAS-B02 SKUs')
        parser.add_argument('--report-dir', default='batch02_reports')
        parser.add_argument('--limit', type=int, help='Process first N images (testing only)')
        parser.add_argument('--production-ack')
        parser.add_argument('--confirm-db-fingerprint')
        parser.add_argument('--backup-file')

    def handle(self, *args, **options):
        if options['limit'] is not None and options['limit'] < 1:
            raise CommandError('--limit must be positive')
        committing = options['commit']
        cloud_mode = getattr(settings, 'STUDENTSTORE_MEDIA_PROVIDER', 'local') == 'r2'
        if committing:
            if not settings.DEBUG:
                verify_production(options)
            try:
                client, bucket = make_r2_client()
                if not settings.DEBUG and bucket != EXPECTED_BUCKET:
                    raise CommandError('Refusing to use a bucket other than the new Student Store bucket.')
            except (ValueError, ImportError) as exc:
                raise CommandError(str(exc)) from exc
            if cloud_mode and getattr(settings, 'R2_DELIVERY_MODE', 'proxy') == 'public' and not getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', None):
                raise CommandError('Public R2 delivery hostname not configured')
        else:
            client, bucket = None, None
        qs = ProductImage.objects.select_related('product').order_by('pk')
        if options['batch_only']:
            qs = qs.filter(product__sku__startswith='OJAS-B02-')
        if options['limit']:
            qs = qs[:options['limit']]
        entries = list(qs)
        base = Path(settings.MEDIA_ROOT)
        counts = Counter()
        report = []
        source = None
        try:
            if options['images']:
                source = ImageSource(options['images'])
            for image in entries:
                outcome = self._move_one(image, base, source, client, bucket,
                                         committing, cloud_mode)
                report.append(outcome)
                counts[outcome['status']] += 1
                if outcome['status'] in ('missing', 'failed'):
                    self.stderr.write(f"Product image #{image.pk} [{image.product.sku}]: "
                                      f"{outcome['status']} — {outcome['detail']}")
        except (OSError, ValueError) as exc:
            raise CommandError(f'Image source error: {exc}') from exc
        finally:
            if source:
                source.close()
        output = self._report(options['report_dir'], report, counts, committing, cloud_mode)
        self.stdout.write(self.style.SUCCESS(f'Image migration status: {dict(counts)}'))
        self.stdout.write('Report: ' + output)
        if committing and not cloud_mode:
            self.stdout.write('STAGED ONLY: default storage remains local. No database image names changed. '
                              'After verifying your R2 settings, switch to r2 and rerun --commit.')
        if committing and cloud_mode:
            self.stdout.write('R2 objects verified and DB references updated where needed. '
                              'Local photographs were NOT deleted.')

    def _move_one(self, image, media_root, source, client, bucket, committing, cloud_mode):
        sku = image.product.sku
        old = image.image.name
        record = {'image_id': image.pk, 'sku': sku, 'old_name': old,
                  'new_name': '', 'status': 'failed', 'detail': ''}
        try:
            if not old:
                return self._result(record, 'missing', 'ProductImage has no name')
            if not old.startswith('products/'):
                # Already unrelated asset? Avoid moving banners or strange paths.
                return self._result(record, 'failed', 'Unexpected image path prefix; review manually')
            number = None
            if re.fullmatch(r'OJAS-B02-\d{4}', sku):
                number = int(sku[-4:])
            extension = Path(old).suffix.lower()
            if extension not in ('.jpg', '.jpeg', '.png', '.webp'):
                return self._result(record, 'failed', 'Image extension not supported')
            if number:
                key = f'products/batch-02/{number:04d}{extension}'
            elif old.startswith('products/legacy/'):
                key = old
            else:
                key = f'products/legacy/{image.pk:08d}{extension}'
            record['new_name'] = key
            try:
                # Prevent ../../ escape; Django ImageField normally sanitizes names,
                # but old import scripts might have inserted raw paths.
                local = (media_root / old).resolve(strict=False)
                if not local.is_relative_to(media_root.resolve()):
                    raise ValueError('Media name escapes MEDIA_ROOT')
                data = local.read_bytes() if local.is_file() and local.stat().st_size <= MAX_IMAGE_BYTES else None
            except (OSError, ValueError):
                data = None
            if data is None and source is not None and number:
                file_hint = (image.product.specifications or {}).get('source_photo_filename', '')
                match = source.match(number, file_hint)
                data = source.read(match)
            if data is None:
                return self._result(record, 'missing', 'No local media file or matching original photo (provide --images)')
            if len(data) > MAX_IMAGE_BYTES:
                return self._result(record, 'failed', 'Photo exceeds size limit')
            if not committing:
                return self._result(record, 'dry_run_ready', 'Source found; R2 is not contacted during dry-run')
            mime = mimetypes.guess_type(key)[0] or 'application/octet-stream'
            action = put_r2_verified(client, bucket, key, data, mime)
            if cloud_mode:
                if old != key:
                    # Only mutate image path; no product, inventory, pricing or order changes.
                    image.image.name = key
                    image.save(update_fields=['image'])
                return self._result(record, 'migrated', f'R2 verified ({action}); path updated as needed')
            return self._result(record, 'staged', f'R2 verified ({action}); DB path unchanged until cloud mode')
        except Exception as exc:
            # Deliberately omit exception text which might contain S3 endpoint/auth details.
            return self._result(record, 'failed', f'{type(exc).__name__}; inspect local error logs privately')

    @staticmethod
    def _result(record, status, detail):
        record['status'], record['detail'] = status, detail
        return record

    @staticmethod
    def _report(folder, records, counts, commit, cloud_mode):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        filename = folder / ('r2_migration_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        summary = {
            'mode': 'commit' if commit else 'dry-run',
            'default_storage_mode': 'r2' if cloud_mode else 'local',
            'counts': dict(counts), 'records': records,
            'safety': 'No prices, SKUs, stock, names, categories, orders, or local files changed.',
        }
        with filename.with_suffix('.json').open('w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        with filename.with_suffix('.csv').open('w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, ('image_id', 'sku', 'old_name', 'new_name', 'status', 'detail'))
            w.writeheader()
            w.writerows(records)
        return f'{filename}.json and {filename}.csv'
