"""Import up to 2000 CSV-matched stationery products without touching existing SKUs."""
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from catalog.batch02.estimates import estimate_prices, estimated_stock, pack_details, sale_name
from catalog.batch02.sources import ImageSource, filename_number, normalized, read_rows, serial_number
from catalog.batch02.storage_ops import save_verified, put_r2_verified, make_r2_client, source_fingerprint
from catalog.batch02.guards import verify_production, db_identity, EXPECTED_BUCKET
from catalog.models import Brand, Category, Product, ProductImage


class Command(BaseCommand):
    help = 'Import OJAS B02 images from ZIP/folder and CSV; dry run by default, safe SKU reruns.'

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument('--dry-run', action='store_true', help='No database or media writes (default)')
        mode.add_argument('--commit', action='store_true', help='Insert approved records')
        parser.add_argument('--csv', dest='csv_path', help='Product catalogue CSV')
        parser.add_argument('--source-dir', help='Directory used to discover catalogue CSV and images')
        parser.add_argument('--images', help='Numbered photograph ZIP or folder')
        parser.add_argument('--storage', choices=['local', 'r2'], default=None)
        parser.add_argument('--report-dir', default='batch02_reports')
        parser.add_argument('--limit', type=int, help='Process first N CSV rows (testing only)')
        parser.add_argument('--production-ack', help='Explicit acknowledgment of Railway production import')
        parser.add_argument('--confirm-db-fingerprint', help='Exact nonsecret fingerprint from target inspection')
        parser.add_argument('--backup-file', help='Fresh pg_dump backup from selected production database')
        parser.add_argument('--approved-dry-run', help='Matching dry-run JSON report from same DB and CSV')
        parser.add_argument('--allow-name-duplicates', action='store_true',
                            help='Allow identical brand/name/pack signatures; review before use')

    def handle(self, *args, **options):
        committing = options['commit']
        provider = getattr(settings, 'STUDENTSTORE_MEDIA_PROVIDER', 'local')
        mode = options['storage'] or provider
        if mode != provider:
            raise CommandError(f'--storage={mode} differs from configured default storage {provider}. '
                               'Set STUDENTSTORE_MEDIA_PROVIDER to match before importing.')
        if committing and not settings.DEBUG and provider != 'r2':
            raise CommandError('Production import requires R2 (Railway local storage is ephemeral).')
        if committing and provider == 'r2':
            for setting in ('AWS_STORAGE_BUCKET_NAME', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY',
                            'AWS_S3_ENDPOINT_URL'):
                if not getattr(settings, setting, ''):
                    raise CommandError(f'R2 must be configured before --commit: {setting} is missing')

        # Fail closed: production database writes only with strong explicit confirmation.
        if committing and provider == 'r2':
            verify_production(options)
        if committing and not settings.DEBUG and provider != 'r2':
            raise CommandError('Never import into ephemeral production media storage.')
        if committing and provider == 'local':
            target = db_identity()
            sqlite_test = target['engine'].endswith('sqlite3')
            if not settings.DEBUG or (not sqlite_test and target['host'].lower() not in {'127.0.0.1', 'localhost', '::1'}):
                raise CommandError('Local image commit permitted only with DEBUG=True and localhost database.')

        base = Path(options['source_dir']) if options['source_dir'] else None
        csv_path = Path(options['csv_path']) if options['csv_path'] else self._discover_csv(base)
        image_path = Path(options['images']) if options['images'] else self._discover_images(base)
        if not csv_path or not csv_path.is_file():
            raise CommandError('CSV not found. Supply --csv "C:\\path\\products.csv" or --source-dir.')
        if not image_path or not image_path.exists():
            raise CommandError('Photos not found. Supply --images "C:\\path\\images.zip" or --source-dir.')
        try:
            rows = read_rows(csv_path)
        except (OSError, ValueError, csv.Error) as exc:
            raise CommandError(f'CSV validation: {exc}') from exc
        if options['limit'] is not None:
            if options['limit'] < 1:
                raise CommandError('--limit must be greater than zero')
            rows = rows[:options['limit']]
        if not rows:
            raise CommandError('CSV contains no product rows')

        from catalog.batch02.storage_ops import digest_stream
        with csv_path.open('rb') as _csv_stream:
            csv_sha256 = digest_stream(_csv_stream)
        image_source_sha256 = source_fingerprint(image_path)
        identity = db_identity()
        if committing and provider == 'r2':
            approval = options.get('approved_dry_run')
            if not approval:
                raise CommandError('Production commit requires --approved-dry-run <dryrun.json>.')
            try:
                approved = json.loads(Path(approval).read_text(encoding='utf-8'))
            except (OSError, ValueError) as exc:
                raise CommandError('Cannot read approved dry-run JSON.') from exc
            if (approved.get('mode') != 'dry-run' or approved.get('storage') != 'r2'
                    or approved.get('csv_sha256') != csv_sha256
                    or approved.get('image_source_sha256') != image_source_sha256
                    or approved.get('row_limit') != options['limit']
                    or approved.get('db_fingerprint') != identity['fingerprint']
                    or approved.get('csv_file') != str(csv_path.resolve())
                    or approved.get('image_source') != str(image_path.resolve())):
                raise CommandError('Approved dry run does not match selected database, CSV, or images location.')
            try:
                r2_client, r2_bucket = make_r2_client()
                if r2_bucket != EXPECTED_BUCKET:
                    raise CommandError('Unexpected R2 bucket: refusing to touch Academy assets.')
                r2_client.head_bucket(Bucket=r2_bucket)
            except CommandError:
                raise
            except Exception as exc:
                raise CommandError(f'R2 preflight failed ({type(exc).__name__}); credentials/bucket not ready.') from None
        else:
            r2_client, r2_bucket = None, None

        started_count = Product.objects.count()
        existing = set(Product.objects.values_list('sku', flat=True))
        # Exact, normalized signatures protect from accidental double-imports.
        signatures = set()
        for name, brand_name in Product.objects.values_list('name', 'brand__name'):
            signatures.add((normalized(name), normalized(brand_name)))
        seen_skus = set()
        seen_signatures = set()
        seen_hashes = {}
        counts = Counter()
        report = []
        self.stdout.write(f'Mode: {"COMMIT" if committing else "DRY RUN"}; storage: {provider}; '
                          f'current products in selected DB: {started_count}; CSV rows: {len(rows)}')
        try:
            with ImageSource(image_path) as images:
                for row in rows:
                    result = self._process(row, images, committing, existing, signatures,
                                           seen_skus, seen_signatures, seen_hashes,
                                           options['allow_name_duplicates'], r2_client, r2_bucket, provider)
                    report.append(result)
                    counts[result['status']] += 1
                    if result['status'] in ('failed', 'missing_image', 'invalid_image', 'image_upload_failure', 'duplicate'):
                        self.stderr.write(f"row {result['line']} {result.get('sku', '')}: "
                                          f"{result['status']}: {result['reason']}")
        except (OSError, ValueError, __import__('zipfile').BadZipFile) as exc:
            raise CommandError(f'Image source error: {exc}') from exc
        end_count = Product.objects.count()
        output = self._write_reports(options['report_dir'], report, counts,
                                     csv_path, image_path, provider, committing,
                                     started_count, end_count, csv_sha256, identity['fingerprint'], image_source_sha256, options['limit'])
        self.stdout.write(self.style.SUCCESS(f'Status counts: {dict(counts)}; '
                                             f'DB total before={started_count}, after={end_count}'))
        self.stdout.write(f'Import reports: {output}')
        self.stdout.write('WARNING: MRP/selling and 12–40 stock figures are planning estimates, '
                          'not verified manufacturer prices or physical inventory.')
        self.stdout.write('Import is local to the connected database; Railway PostgreSQL is NOT changed automatically.')

    def _process(self, row, images, committing, existing, signatures,
                 seen_skus, seen_signatures, seen_hashes, allow_dupes, r2_client, r2_bucket, provider):
        result = {'line': row['line'], 'sku': '', 'image_number': '', 'image_filename': '',
                  'status': 'failed', 'reason': '', 'requires_review': [],
                  'estimated_stock': '', 'mrp_estimate': '', 'selling_estimate': '',
                  'pack_csv': row['pack']}
        try:
            source_n = row['serial'] or row['sku']
            if not source_n and row['image_file']:
                source_n = filename_number(Path(row['image_file'].replace('\\', '/')).name)
            n = serial_number(source_n)
            sku = f'OJAS-B02-{n:04d}'
            result['sku'], result['image_number'] = sku, n
            if row['sku'] and row['serial'] and row['sku'].upper().startswith('OJAS-B02-'):
                if serial_number(row['sku']) != n:
                    return self._skip(result, 'failed', 'Conflicting CSV serial/photo number and batch SKU')
            if sku in seen_skus:
                return self._skip(result, 'duplicate', 'Repeated image number/SKU inside CSV')
            seen_skus.add(sku)
            if sku in existing:
                return self._skip(result, 'existing_sku', 'SKU already exists; existing data left completely unchanged')
            if not row['name'].strip() or not row['category'].strip():
                return self._skip(result, 'failed', 'Product name/category is missing')
            if len(row['category']) > 120 or len(row['brand']) > 100:
                return self._skip(result, 'failed', 'Category/brand exceeds Django field length')
            pack, multiplier, uncertain = pack_details(row['pack'], row['name'])
            if uncertain or row.get('pack_unverified_source'):
                result['requires_review'].append('unverified pack quantity / CSV variant')
            name = sale_name(row['name'], pack)
            signature = (normalized(name), normalized(row['brand']))
            if (signature in signatures or signature in seen_signatures) and not allow_dupes:
                return self._skip(result, 'duplicate', 'Existing or repeated product name + brand; manual review required')
            try:
                img_name = images.match(n, row['image_file'])
            except ValueError as exc:
                return self._skip(result, 'missing_image', str(exc))
            result['image_filename'] = img_name
            try:
                photo = images.read(img_name)
            except (OSError, ValueError) as exc:
                return self._skip(result, 'invalid_image', str(exc))
            digest = hashlib.sha256(photo).hexdigest()
            if digest in seen_hashes:
                # Distinct color/pack variants can share a manufacturer image;
                # flag but do not assume they are the same saleable SKU.
                result['requires_review'].append(f'photograph reused by {seen_hashes[digest]}')
            seen_hashes.setdefault(digest, sku)
            mrp, selling = estimate_prices(row, multiplier)
            stock = estimated_stock(sku)
            result.update(estimated_stock=stock, mrp_estimate=str(mrp),
                          selling_estimate=str(selling or mrp))
            if not row['mrp']:
                result['requires_review'].append('estimated MRP not verified')
            else:
                result['requires_review'].append('CSV MRP not manufacturer-verified')
            result['requires_review'].append('stock is estimated, not physical stock')
            if not row['brand']:
                result['requires_review'].append('brand missing from CSV')
            if not committing:
                seen_signatures.add(signature)
                result['status'] = 'ready_dry_run'
                return result

            # Stable, non-colliding namespace. No user-controlled path components.
            suffix = Path(img_name).suffix.lower()
            key = f'products/batch-02/{n:04d}{suffix}'
            # Storage IO occurs first so no product row is committed without its image.
            try:
                result['image_upload'] = (put_r2_verified(r2_client, r2_bucket, key, photo,
                                                       __import__('mimetypes').guess_type(key)[0] or 'application/octet-stream')
                                          if provider == 'r2' else save_verified(default_storage, key, photo))
            except ValueError as exc:
                # Known safe validation errors contain no secrets.
                return self._skip(result, 'image_upload_failure', str(exc))
            except Exception as exc:
                return self._skip(result, 'image_upload_failure',
                                  f'{type(exc).__name__}; inspect storage privately')
            with transaction.atomic():
                # Skip concurrent/existing SKUs rather than update a product.
                if Product.objects.filter(sku=sku).exists():
                    return self._skip(result, 'existing_sku', 'SKU created concurrently; unchanged')
                cat = self._category(row['category'])
                brand = self._brand(row['brand'])
                specs = {
                    'source_batch': 'OJAS-B02', 'source_photo_number': n,
                    'source_photo_filename': Path(img_name).name,
                    'pricing_review_required': True, 'stock_is_estimate': True,
                    'pack_quantity': pack, 'pack_review_required': bool(uncertain or row.get('pack_unverified_source')),
                }
                if row['subcategory']:
                    specs['subcategory'] = row['subcategory']  # No breaking schema migration.
                description = row['description'].strip() or self._description(name, row['brand'], row['category'], pack)
                product = Product.objects.create(
                    sku=sku, slug=slugify(sku), name=name, description=description,
                    category=cat, brand=brand, product_type=Product.ProductType.PHYSICAL,
                    price=mrp, discount_price=selling, stock=stock, is_active=True,
                    specifications=specs,
                )
                ProductImage.objects.create(product=product, image=key, alt_text=name[:255], position=0)
            result['status'] = 'imported'
            existing.add(sku)
            seen_signatures.add(signature)
            signatures.add(signature)
            return result
        except ValueError as exc:
            return self._skip(result, 'failed', str(exc))
        except Exception as exc:
            # Deliberately do not log exception repr: third-party SDK errors can include request URLs.
            return self._skip(result, 'failed', f'{type(exc).__name__}; inspect credentials, storage and DB logs without sharing secrets')

    @staticmethod
    def _skip(result, status, reason):
        result['status'] = status
        result['reason'] = reason
        return result

    @staticmethod
    def _category(name):
        name = name.strip()
        existing = Category.objects.filter(name__iexact=name).first()
        if existing:
            if not existing.is_active:
                raise ValueError('Matching category is inactive; refusing to silently activate or duplicate')
            return existing
        slug = slugify(name)[:50]
        if not slug:
            raise ValueError('Category needs a usable slug')
        existing = Category.objects.filter(slug=slug).first()
        if existing:
            raise ValueError('Category slug already belongs to a different name; manual mapping required')
        return Category.objects.create(name=name, slug=slug, is_active=True)

    @staticmethod
    def _brand(name):
        name = name.strip()
        if not name:
            return None
        existing = Brand.objects.filter(name__iexact=name).first()
        if existing:
            return existing
        slug = slugify(name)[:50]
        if not slug:
            raise ValueError('Brand needs a usable slug')
        if Brand.objects.filter(slug=slug).exists():
            raise ValueError('Brand slug already exists for a different name; manual mapping required')
        return Brand.objects.create(name=name, slug=slug)

    @staticmethod
    def _description(name, brand, category, pack):
        # Only factually grounded CSV terms, no fabricated claims (quality, size, etc.).
        info = [name]
        if brand:
            info.append(f'Brand: {brand}')
        if category:
            info.append(f'Category: {category}')
        if pack:
            info.append(f'Pack: {pack}')
        return '. '.join(info) + '.'

    @staticmethod
    def _discover_csv(base):
        if base and base.is_dir():
            paths = [p for p in base.rglob('*.csv') if not p.name.lower().startswith(('report', 'import_result', 'batch02_'))]
            candidates = []
            for p in paths:
                try:
                    read_rows(p)
                except (OSError, ValueError, csv.Error, UnicodeError):
                    continue
                candidates.append(p)
            if len(candidates) == 1:
                return candidates[0]
            if candidates:
                raise CommandError('Multiple product CSVs found. Specify --csv explicitly: ' + ', '.join(map(str, candidates[:5])))
        return None

    @staticmethod
    def _discover_images(base):
        if not base or not base.exists():
            return None
        if base.is_dir():
            zips = [p for p in base.glob('*.zip') if 'image' in p.name.lower()]
            if len(zips) == 1:
                return zips[0]
            return base
        return base

    @staticmethod
    def _write_reports(directory, data, counts, csv_path, image_path, provider, commit, before, after, csv_sha256, db_fingerprint, image_source_sha256, row_limit):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        suffix = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        basename = directory / f'batch02_{"commit" if commit else "dryrun"}_{suffix}'
        summary = {'mode': 'commit' if commit else 'dry-run', 'storage': provider,
                   'csv_file': str(csv_path.resolve()), 'image_source': str(image_path.resolve()),
                   'csv_sha256': csv_sha256, 'db_fingerprint': db_fingerprint,
                   'image_source_sha256': image_source_sha256, 'row_limit': row_limit,
                   'counts': dict(counts), 'db_products_before': before,
                   'db_products_after': after,
                   'disclaimer': 'Stock 12–40 units is ESTIMATED, not counted inventory. Prices are estimates or UNVERIFIED CSV references, NOT validated manufacturer MRPs. Review before real orders.',
                   'records': data}
        with (basename.with_suffix('.json')).open('w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        with (basename.with_suffix('.csv')).open('w', encoding='utf-8-sig', newline='') as f:
            fields = ('line', 'sku', 'image_number', 'image_filename', 'status', 'reason',
                      'requires_review', 'pack_csv', 'estimated_stock', 'mrp_estimate',
                      'selling_estimate', 'image_upload')
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            for record in data:
                writer.writerow({**record, 'requires_review': ' | '.join(record['requires_review'])})
        return f'{basename}.json and {basename}.csv'
