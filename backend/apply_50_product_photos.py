"""Add user-provided product photos as primary images; dry-run by default."""
import argparse
import os
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
import django
django.setup()
from django.db import transaction
from django.core.files import File
from catalog.models import Product, ProductImage

parser = argparse.ArgumentParser()
parser.add_argument("photo_folder")
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()
folder = Path(args.photo_folder)
if not folder.is_dir():
    parser.error("Photo folder not found: " + str(folder))
missing = []
ready = []
for n in range(1, 51):
    sku = f"STU-{n:03d}"
    photo = folder / f"stu-{n:03d}.jpg"
    try:
        product = Product.objects.get(sku=sku)
    except Product.DoesNotExist:
        missing.append(sku + " (missing product)")
        continue
    if not photo.is_file():
        missing.append(sku + " (missing photo)")
        continue
    if photo.stat().st_size < 1000:
        missing.append(sku + " (invalid/empty photo)")
        continue
    already = product.images.filter(image__icontains=f"stu-{n:03d}-photo-").exists()
    ready.append((product, photo, already))
print(f"Found {len(ready)} matching SKU/photo pairs; {len(missing)} missing; {sum(x[2] for x in ready)} previously attached")
for entry in missing:
    print("WARNING:", entry)
if missing:
    raise SystemExit("Aborting due to missing files/products. No changes made.")
if not args.apply:
    print("DRY RUN: no changes. Use --apply after reviewing IMAGE_REVIEW.csv.")
    raise SystemExit(0)
added = 0
for product, photo, already in ready:
    if already:
        continue
    # Keep existing illustrations as secondary images for rollback/review.
    with transaction.atomic():
        ProductImage.objects.filter(product=product).update(position=10)
        new = ProductImage(product=product, alt_text=f"{product.name} — user supplied product photograph", position=0)
        with photo.open("rb") as handle:
            new.image.save(f"{product.sku.lower()}-photo-{photo.name}", File(handle), save=False)
        new.save()
    added += 1
print(f"COMPLETE: {added} new primary photos added; {len(ready)-added} skipped. Prices/stock unchanged.")
