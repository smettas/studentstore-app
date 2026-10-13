"""Attach user-supplied images for STU-051..STU-200 as primary images. Dry run by default."""
import argparse
import hashlib
import os
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
import django
django.setup()
from django.core.files import File
from django.db import transaction
from catalog.models import Product, ProductImage

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('photo_folder', help='Path to extracted photos folder')
parser.add_argument('--apply', action='store_true', help='Write changes to database and storage')
args = parser.parse_args()
folder = Path(args.photo_folder)
if not folder.is_dir():
    parser.error('Photo folder does not exist: ' + str(folder))

ready, problems = [], []
for n in range(51, 201):
    sku = f'STU-{n:03d}'
    path = folder / f'stu-{n:03d}.jpg'
    product = Product.objects.filter(sku=sku).first()
    if product is None:
        problems.append(f'{sku}: missing product in database')
        continue
    if not path.is_file() or path.stat().st_size < 1000:
        problems.append(f'{sku}: missing or empty image')
        continue
    with path.open('rb') as file:
        magic = file.read(3)
    if magic[:2] != b'\xff\xd8':
        problems.append(f'{sku}: image is not a valid JPEG file')
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    marker = f'{sku.lower()}-customer-photo-{digest}'
    existing = ProductImage.objects.filter(product=product, image__icontains=marker).exists()
    ready.append((product, path, marker, existing))

print(f'Validated {len(ready)} SKU/photo pairs; {len(problems)} problems; {sum(item[3] for item in ready)} already attached.')
for problem in problems:
    print('ERROR:', problem)
if problems:
    raise SystemExit('Stopped: no changes applied. Resolve all errors first.')
if not args.apply:
    print('DRY RUN ONLY. Review IMAGE_REVIEW.csv, then add --apply to attach photos.')
    raise SystemExit(0)

created = skipped = 0
for product, path, marker, existing in ready:
    if existing:
        skipped += 1
        continue
    with transaction.atomic():
        # Keep older images as secondary for reference and rollback.
        ProductImage.objects.filter(product=product).update(position=10)
        photo = ProductImage(product=product, position=0, alt_text=f'{product.name} — user-provided product photo')
        with path.open('rb') as source:
            photo.image.save(f'{marker}.jpg', File(source), save=False)
        photo.save()
    created += 1
print(f'COMPLETE: {created} new primary images attached; {skipped} already attached.')
print('Product prices, stock, descriptions, and active status were not changed.')
