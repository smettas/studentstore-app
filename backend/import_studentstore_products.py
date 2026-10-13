"""Import the StudentStore draft catalogue into Django/PostgreSQL.

Usage (from backend directory):
  python import_studentstore_products.py "C:\\Users\\YOU\\Downloads\\studentstore_products_200_draft.xlsx"
  python import_studentstore_products.py "C:\\Users\\YOU\\Downloads\\studentstore_products_200_draft.xlsx" --apply

Default is a dry run. Imported drafts are inactive with zero stock; price=0.00
is a placeholder required by the current Product model, NOT a selling price.
Existing products are skipped, never overwritten. Images are not imported.
"""
import argparse
import os
import sys
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path


def value(row, key):
    v = row.get(key)
    return str(v).strip() if v is not None else ""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path, help="Path to the catalogue .xlsx")
    parser.add_argument("--apply", action="store_true", help="Write draft records to database")
    args = parser.parse_args()
    if not args.workbook.is_file():
        parser.error(f"Workbook not found: {args.workbook}")

    try:
        from openpyxl import load_workbook
    except ImportError:
        parser.error("Install Excel reader first: python -m pip install openpyxl")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    import django
    django.setup()
    from django.db import transaction
    from django.utils.text import slugify
    from catalog.models import Brand, Category, Product, StudyLevel

    wb = load_workbook(args.workbook, read_only=True, data_only=True)
    if "Products" not in wb.sheetnames:
        parser.error("Workbook has no 'Products' worksheet")
    rows = wb["Products"].iter_rows(values_only=True)
    headers = next(rows, None)
    if not headers:
        parser.error("Products worksheet is empty")
    required = {"SKU", "Product Name", "Category", "Brand (proposed)", "Description (draft)", "Study Level (suggested)", "MRP (INR)", "Selling Price (INR)", "Stock Qty", "Status"}
    if not required.issubset(set(headers)):
        parser.error(f"Missing columns: {sorted(required - set(headers))}")
    records = [dict(zip(headers, cells)) for cells in rows if any(x is not None for x in cells)]
    errors = []
    skus = set()
    for n, r in enumerate(records, start=2):
        sku, name, category = (value(r, k) for k in ("SKU", "Product Name", "Category"))
        if not sku or not name or not category:
            errors.append(f"Row {n}: SKU, name and category required")
        if sku in skus:
            errors.append(f"Row {n}: duplicate SKU {sku}")
        skus.add(sku)
        if len(sku) > 64 or len(name) > 255 or len(category) > 120:
            errors.append(f"Row {n}: a field exceeds its database length")
        status = value(r, "Status").upper()
        if status != "DRAFT":
            errors.append(f"Row {n}: only DRAFT rows are supported (found {status!r})")
        if value(r, "Selling Price (INR)"):
            try:
                if Decimal(value(r, "Selling Price (INR)")) < 0:
                    errors.append(f"Row {n}: negative selling price")
            except InvalidOperation:
                errors.append(f"Row {n}: invalid selling price")
    if errors:
        print("Validation failed:\n" + "\n".join(errors[:30]))
        sys.exit(1)

    print(f"Validated {len(records)} draft products across {len(set(value(r, 'Category') for r in records))} categories.")
    print("Import policy: inactive products, zero stock, placeholder price 0.00; no image uploads.")
    existing = set(Product.objects.filter(sku__in=skus).values_list("sku", flat=True))
    print(f"Existing SKUs to skip: {len(existing)}; new products: {len(records) - sum(value(r, 'SKU') in existing for r in records)}")
    if not args.apply:
        print("DRY RUN ONLY. Add --apply to create draft records.")
        return

    created = Counter()
    with transaction.atomic():
        for r in records:
            sku = value(r, "SKU")
            if sku in existing:
                created["skipped"] += 1
                continue
            category_name = value(r, "Category")
            category_slug = slugify(category_name)
            category, _ = Category.objects.get_or_create(slug=category_slug, defaults={"name": category_name, "is_active": True})
            brand_name = value(r, "Brand (proposed)")
            brand = None
            if brand_name and brand_name.lower() not in {"generic", "unbranded", "to confirm"}:
                brand, _ = Brand.objects.get_or_create(slug=slugify(brand_name), defaults={"name": brand_name})
            # Use SKU in slug so repeated product names cannot collide.
            slug = slugify(sku)
            if Product.objects.filter(slug=slug).exists():
                raise ValueError(f"Slug collision for {sku}: {slug}")
            product = Product.objects.create(
                sku=sku, slug=slug, name=value(r, "Product Name"),
                description=value(r, "Description (draft)"), category=category,
                brand=brand, product_type=Product.ProductType.PHYSICAL,
                price=Decimal("0.00"), discount_price=None, stock=0,
                is_active=False,
            )
            levels = [s.strip() for s in value(r, "Study Level (suggested)").split("/") if s.strip()]
            for level_name in levels:
                level, _ = StudyLevel.objects.get_or_create(slug=slugify(level_name), defaults={"name": level_name})
                product.study_levels.add(level)
            created["products"] += 1
    print(f"COMPLETE: {created['products']} inactive drafts created; {created['skipped']} existing products skipped.")
    print("To publish later, verify descriptions, actual prices, stock and authorized images individually.")


if __name__ == "__main__":
    main()
