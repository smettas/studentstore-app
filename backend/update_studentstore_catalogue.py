"""Update 200 existing StudentStore draft products from the package CSV.

From backend directory:
  python update_studentstore_catalogue.py "C:\\Users\\YOU\\Downloads\\StudentStore_200_Products_Professional_Package.zip"
  python update_studentstore_catalogue.py "C:\\Users\\YOU\\Downloads\\StudentStore_200_Products_Professional_Package.zip" --apply

Images are original illustrations, NOT genuine branded product photographs.
Pricing is estimated, stock is suggested (not physically verified).
Products remain inactive for safe review. Requires MEDIA storage configured.
"""
import argparse,csv,io,os,zipfile
from decimal import Decimal
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('package',type=Path)
 p.add_argument('--apply',action='store_true')
 args=p.parse_args()
 if not args.package.is_file():p.error('ZIP not found')
 os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.local')
 import django;django.setup()
 from django.db import transaction
 from django.core.files.base import ContentFile
 from catalog.models import Product,ProductImage
 with zipfile.ZipFile(args.package) as z:
  data=list(csv.DictReader(io.StringIO(z.read('catalogue.csv').decode('utf-8-sig'))))
  if len(data)!=200:raise ValueError(f'Expected 200 rows, found {len(data)}')
  skus=[r['SKU'] for r in data]
  if len(set(skus))!=200:raise ValueError('Duplicate SKUs')
  existing={p.sku:p for p in Product.objects.filter(sku__in=skus)}
  missing=set(skus)-set(existing)
  if missing:raise ValueError(f'{len(missing)} products missing. Import the original draft catalogue first. Examples: {sorted(missing)[:5]}')
  for r in data:
   if r['Status']!='DRAFT':raise ValueError('Only DRAFT rows allowed')
   for field in ('MRP (INR, estimate)','Selling Price (INR, estimate)'):
    if Decimal(r[field])<=0:raise ValueError(f'Invalid {field}: {r["SKU"]}')
   if int(r['Suggested Stock Qty (not physical inventory)'])<0:raise ValueError('Invalid stock')
   if r['Image Filename'] not in z.namelist():raise ValueError('Missing image: '+r['Image Filename'])
  print(f'VALIDATED: {len(data)} products, {len(data)} images. Price estimates and illustrative photos ONLY.')
  print('All products remain INACTIVE. Suggested stock is NOT confirmed inventory.')
  if not args.apply:
   print('DRY RUN. Add --apply to update existing product records and attach illustrations.')
   return
  updated=0;attached=0
  with transaction.atomic():
   for r in data:
    product=existing[r['SKU']]
    product.description=r['Description']+'\n\nSpecifications (unverified): '+r['Specifications (verify)']
    product.price=Decimal(r['MRP (INR, estimate)'])
    product.discount_price=Decimal(r['Selling Price (INR, estimate)'])
    product.stock=int(r['Suggested Stock Qty (not physical inventory)'])
    product.is_active=False
    product.save(update_fields=['description','price','discount_price','stock','is_active','updated_at'])
    if not product.images.exists():
     img=ProductImage(product=product,alt_text=f'Illustrative artwork for {product.name}; not actual product photograph',position=0)
     img.image.save(Path(r['Image Filename']).name,ContentFile(z.read(r['Image Filename'])),save=True)
     attached+=1
    updated+=1
  print(f'COMPLETE: {updated} existing draft products updated; {attached} illustrative images attached. Products remain inactive.')
  print('NOTE: Image uploads use your configured Django storage; check MEDIA settings and storage credentials before --apply.')
if __name__=='__main__':main()
