"""Database and file-based regression tests using SQLite test-only settings."""
import csv
import io
import tempfile
import zipfile
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image

from catalog.batch02.estimates import estimated_stock, estimate_prices, pack_details
from catalog.batch02.sources import ImageSource, read_rows
from catalog.models import Category, Product, ProductImage


def jpeg(seed):
    output = io.BytesIO()
    Image.new('RGB', (4, 4), (seed * 50, 75, 111)).save(output, 'JPEG')
    return output.getvalue()


class Batch02Tests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.csv = self.root / 'products.csv'
        self.zip = self.root / 'photos.zip'
        self.media = self.root / 'media'
        self.media.mkdir()
        with self.csv.open('w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Serial', 'Product Name', 'Category', 'Brand', 'Pack Quantity', 'Description'])
            writer.writerow(['0002', 'Ball Pen', 'Pens & Writing Instruments', 'Cello', 'Pack of 5', 'Ball pen pack.'])
            writer.writerow(['0001', 'Colour Pencils', 'Art & Craft Supplies', 'Camlin', '12 Colours', 'Colour pencils set.'])
        with zipfile.ZipFile(self.zip, 'w') as z:
            z.writestr('photos/0001.jpg', jpeg(1))
            z.writestr('photos/0002.jpg', jpeg(2))
        self.storage = override_settings(MEDIA_ROOT=str(self.media), STUDENTSTORE_MEDIA_PROVIDER='local', DEBUG=True)
        self.storage.enable()
        self.addCleanup(self.storage.disable)

    def run_import(self, **kwargs):
        out = io.StringIO()
        call_command('import_ojas_batch02', csv_path=str(self.csv), images=str(self.zip),
                     report_dir=str(self.root / 'reports'), stdout=out, stderr=io.StringIO(), **kwargs)
        return out.getvalue()

    def test_dry_run_has_no_db_or_storage_effects(self):
        self.run_import(dry_run=True)
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(list(self.media.rglob('*')), [])

    def test_commit_real_numbers_active_and_rerun_preserves_stock_price_image(self):
        Product.objects.create(sku='PRE-1', name='Existing', slug='existing',
                               category=Category.objects.create(name='Original', slug='original'),
                               price=Decimal('89'), stock=9, is_active=True)
        self.run_import(commit=True)
        self.assertEqual(Product.objects.count(), 3)
        p1 = Product.objects.get(sku='OJAS-B02-0001')
        p2 = Product.objects.get(sku='OJAS-B02-0002')
        self.assertTrue(p1.is_active and p2.is_active)
        self.assertTrue(12 <= p1.stock <= 40)
        self.assertEqual(p2.specifications['pack_quantity'], 'Pack of 5')
        self.assertEqual(p1.specifications['pack_quantity'], '12 Colours')
        self.assertEqual(p1.images.count(), 1)
        self.assertEqual(p2.images.count(), 1)
        self.assertEqual(Path(self.media / p1.images.first().image.name).read_bytes(), jpeg(1))
        self.assertEqual(Path(self.media / p2.images.first().image.name).read_bytes(), jpeg(2))
        self.assertLessEqual(p2.discount_price or p2.price, p2.price)
        original = (p2.stock, p2.price, p2.images.first().image.name)
        p2.stock = 2  # A real stock adjustment by a person must never be overwritten.
        p2.save(update_fields=['stock'])
        self.run_import(commit=True)
        p2.refresh_from_db()
        self.assertEqual((p2.stock, p2.price, p2.images.first().image.name), (2, original[1], original[2]))
        self.assertEqual(ProductImage.objects.count(), 2)
        self.assertEqual(Product.objects.get(sku='PRE-1').stock, 9)

    def test_missing_photo_skipped_without_product(self):
        with zipfile.ZipFile(self.zip, 'w') as z:
            z.writestr('photos/0001.jpg', jpeg(1))
        self.run_import(commit=True)
        self.assertFalse(Product.objects.filter(sku='OJAS-B02-0002').exists())
        self.assertTrue(Product.objects.filter(sku='OJAS-B02-0001').exists())

    def test_explicit_csv_image_mismatch_rejected(self):
        with self.csv.open('w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Serial', 'Product Name', 'Category', 'Image Filename'])
            writer.writerow([1, 'Gel Pen', 'Pens', '0002.jpg'])
        self.run_import(commit=True)
        self.assertEqual(Product.objects.count(), 0)

    def test_migration_stage_then_switch_r2_without_changing_product(self):
        self.run_import(commit=True)
        p = Product.objects.get(sku='OJAS-B02-0001')
        image = p.images.first()
        before = (p.pk, p.sku, p.price, p.stock, p.name, p.category_id)
        with patch('catalog.management.commands.migrate_catalog_images_to_r2.make_r2_client',
                   return_value=(object(), 'bucket')), \
             patch('catalog.management.commands.migrate_catalog_images_to_r2.put_r2_verified',
                   return_value='uploaded') as put:
            call_command('migrate_catalog_images_to_r2', commit=True, batch_only=True,
                         report_dir=str(self.root / 'reports'), stdout=io.StringIO(), stderr=io.StringIO())
            self.assertEqual(put.call_count, 2)
        image.refresh_from_db()
        old = image.image.name
        with override_settings(STUDENTSTORE_MEDIA_PROVIDER='r2', AWS_S3_CUSTOM_DOMAIN='pub.test.r2.dev'):
            with patch('catalog.management.commands.migrate_catalog_images_to_r2.make_r2_client',
                       return_value=(object(), 'bucket')), \
                 patch('catalog.management.commands.migrate_catalog_images_to_r2.put_r2_verified',
                       return_value='reused'):
                call_command('migrate_catalog_images_to_r2', commit=True, batch_only=True,
                             report_dir=str(self.root / 'reports'), stdout=io.StringIO(), stderr=io.StringIO())
        p.refresh_from_db()
        image.refresh_from_db()
        self.assertEqual(image.image.name, old)
        self.assertEqual((p.pk, p.sku, p.price, p.stock, p.name, p.category_id), before)

    def test_migration_failure_preserves_original_image(self):
        self.run_import(commit=True)
        image = Product.objects.get(sku='OJAS-B02-0001').images.first()
        old = image.image.name
        with override_settings(STUDENTSTORE_MEDIA_PROVIDER='r2', AWS_S3_CUSTOM_DOMAIN='pub.test.r2.dev'):
            with patch('catalog.management.commands.migrate_catalog_images_to_r2.make_r2_client',
                       return_value=(object(), 'bucket')), \
                 patch('catalog.management.commands.migrate_catalog_images_to_r2.put_r2_verified',
                       side_effect=RuntimeError('cloud unavailable')):
                call_command('migrate_catalog_images_to_r2', commit=True, batch_only=True,
                             report_dir=str(self.root / 'reports'), stdout=io.StringIO(), stderr=io.StringIO())
        image.refresh_from_db()
        self.assertEqual(image.image.name, old)

    def test_r2_fallback_reads_original_zip_after_local_media_is_lost(self):
        self.run_import(commit=True)
        photo = Product.objects.get(sku='OJAS-B02-0001').images.first()
        (self.media / photo.image.name).unlink()
        original = photo.image.name
        with override_settings(STUDENTSTORE_MEDIA_PROVIDER='r2', AWS_S3_CUSTOM_DOMAIN='pub.test.r2.dev'):
            with patch('catalog.management.commands.migrate_catalog_images_to_r2.make_r2_client',
                       return_value=(object(), 'bucket')), \
                 patch('catalog.management.commands.migrate_catalog_images_to_r2.put_r2_verified',
                       return_value='uploaded') as mocked:
                call_command('migrate_catalog_images_to_r2', commit=True, batch_only=True,
                             images=str(self.zip), report_dir=str(self.root / 'reports'),
                             stdout=io.StringIO(), stderr=io.StringIO())
                self.assertEqual(mocked.call_count, 2)
                # Photo 0001 is present in one of the verified uploads.
                self.assertTrue(any(call.args[3] == jpeg(1) for call in mocked.call_args_list))
        photo.refresh_from_db()
        self.assertEqual(photo.image.name, original)

    def test_legacy_image_path_is_not_changed_when_cloud_upload_fails(self):
        original_product = Product.objects.create(
            sku='LEGACY-1', slug='legacy-1', name='Old Product', price=Decimal('35'),
            stock=9, category=Category.objects.create(name='Legacy', slug='legacy'))
        media_name = 'products/2026/11/old.jpg'
        (self.media / 'products/2026/11').mkdir(parents=True)
        (self.media / media_name).write_bytes(jpeg(1))
        photo = ProductImage.objects.create(product=original_product, image=media_name)
        with override_settings(STUDENTSTORE_MEDIA_PROVIDER='r2', AWS_S3_CUSTOM_DOMAIN='pub.test.r2.dev'):
            with patch('catalog.management.commands.migrate_catalog_images_to_r2.make_r2_client',
                       return_value=(object(), 'bucket')), \
                 patch('catalog.management.commands.migrate_catalog_images_to_r2.put_r2_verified',
                       side_effect=RuntimeError('upload unavailable')):
                call_command('migrate_catalog_images_to_r2', commit=True,
                             report_dir=str(self.root / 'reports'),
                             stdout=io.StringIO(), stderr=io.StringIO())
        photo.refresh_from_db()
        self.assertEqual(photo.image.name, media_name)
        original_product.refresh_from_db()
        self.assertEqual(original_product.stock, 9)

    def test_estimates_pack_does_not_count_colours_as_12_separate_sets(self):
        pack, factor, uncertain = pack_details('12 Colours', 'Colour Pencils')
        self.assertEqual(factor, 1)
        self.assertFalse(uncertain)
        single = estimate_prices({'name':'Gel Pen','category':'Pens','brand':'','mrp':'','selling':''}, 1)[0]
        multi = estimate_prices({'name':'Gel Pen','category':'Pens','brand':'','mrp':'','selling':''}, 5)[0]
        self.assertGreater(multi, single)
        self.assertEqual(estimated_stock('OJAS-B02-0010'), estimated_stock('OJAS-B02-0010'))
        self.assertTrue(12 <= estimated_stock('OJAS-B02-0010') <= 40)

    def test_csv_and_image_folder_also_work(self):
        folder = self.root / 'numbered'
        folder.mkdir()
        (folder / '0001.jpg').write_bytes(jpeg(1))
        with ImageSource(folder) as source:
            self.assertEqual(source.read(source.match(1)), jpeg(1))
        self.assertEqual(len(read_rows(self.csv)), 2)

    def test_public_api_exposes_active_product_and_real_image_field(self):
        self.run_import(commit=True)
        response = self.client.get('/api/catalog/products/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 2)
        self.assertTrue(data['results'][0]['primary_image']['image_url'])
        response = self.client.get('/api/catalog/products/ojas-b02-0001/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['sku'], 'OJAS-B02-0001')
        self.assertEqual(response.json()['pack_quantity'], '12 Colours')
        response = self.client.get('/api/catalog/products/?pack_quantity=Pack%20of%205')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(response.json()['results'][0]['sku'], 'OJAS-B02-0002')


class R2StorageUnitTests(TestCase):
    """No network: exercise Cloudflare S3-compatible collision protection."""

    def test_r2_upload_verified_repeat_and_collision_protection(self):
        from botocore.exceptions import ClientError
        from catalog.batch02.storage_ops import put_r2_verified
        class Cloud:
            def __init__(self):
                self.objects = {}
                self.writes = 0
            def head_object(self, Bucket, Key):
                if Key not in self.objects:
                    raise ClientError({'Error': {'Code':'404'},
                                       'ResponseMetadata': {'HTTPStatusCode':404}}, 'HeadObject')
                value = self.objects[Key]
                return {'Metadata': value['Metadata'], 'ContentLength': len(value['Body'])}
            def put_object(self, Bucket, Key, Body, ContentType, Metadata, IfNoneMatch):
                assert IfNoneMatch == '*'
                assert Key not in self.objects
                self.objects[Key] = {'Body': Body, 'Metadata': Metadata}
                self.writes += 1
            def get_object(self, Bucket, Key):
                return {'Body': io.BytesIO(self.objects[Key]['Body'])}
        cloud = Cloud()
        key = 'studentstore/products/batch-02/0001.jpg'
        self.assertEqual(put_r2_verified(cloud, 'test-bucket', key, jpeg(1)), 'uploaded')
        self.assertEqual(put_r2_verified(cloud, 'test-bucket', key, jpeg(1)), 'reused')
        with self.assertRaisesRegex(ValueError, 'collision'):
            put_r2_verified(cloud, 'test-bucket', key, jpeg(2))
        self.assertEqual(cloud.writes, 1)

    def test_filename_number_is_strict(self):
        from catalog.batch02.sources import filename_number
        self.assertEqual(filename_number('photo_0011.jpg'), 11)
        self.assertIsNone(filename_number('pen_100mm_blue.jpg'))

class ProductionSafetyAndDeliveryTests(TestCase):
    """Test production guardrails with isolated database and mocked cloud only."""

    def test_production_requires_flags_and_never_accepts_local_database(self):
        from django.core.management.base import CommandError
        from catalog.batch02.guards import verify_production
        with override_settings(DEBUG=False, STUDENTSTORE_MEDIA_PROVIDER='r2',
                               AWS_STORAGE_BUCKET_NAME='ojasone-studentstore'):
            with self.assertRaises(CommandError):
                verify_production({})
            with self.assertRaises(CommandError):
                verify_production({'production_ack':'IMPORT-OJAS-B02-TO-RAILWAY'})

    def test_private_proxy_only_serves_active_catalogue_images(self):
        import tempfile
        from pathlib import Path
        from catalog.models import ProductImage
        category = Category.objects.create(name='Art', slug='art')
        product = Product.objects.create(name='Draw', slug='draw', sku='DRAW-1',
                                         category=category, price=Decimal('19'), stock=12)
        key = 'products/batch-02/0003.jpg'
        ProductImage.objects.create(product=product, image=key)
        with tempfile.TemporaryDirectory() as media:
            target = Path(media) / key
            target.parent.mkdir(parents=True)
            target.write_bytes(jpeg(1))
            with override_settings(STUDENTSTORE_MEDIA_PROVIDER='r2', R2_DELIVERY_MODE='proxy',
                                   MEDIA_ROOT=media):
                result = self.client.get('/api/media/' + key)
                self.assertEqual(result.status_code, 200)
                self.assertEqual(b''.join(result.streaming_content), jpeg(1))
                self.assertEqual(self.client.get('/api/media/products/../../etc/passwd').status_code, 404)
                self.assertEqual(self.client.get('/api/media/products/batch-02/missing.jpg').status_code, 404)
                product.is_active = False
                product.save(update_fields=['is_active'])
                self.assertEqual(self.client.get('/api/media/' + key).status_code, 404)

    def test_proxy_url_preserves_private_key_with_no_domain(self):
        from core.storage.backends import PublicProductMediaStorage
        with override_settings(R2_DELIVERY_MODE='proxy'):
            self.assertEqual(PublicProductMediaStorage().url('products/batch-02/0011.jpg'),
                             '/api/media/products/batch-02/0011.jpg')

    def test_production_import_requires_matching_dry_run_and_mocked_r2(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from catalog.batch02.storage_ops import put_r2_verified
        from catalog.batch02.guards import db_identity
        from botocore.exceptions import ClientError

        class FakeCloud:
            def __init__(self): self.objects = {}; self.writes = 0
            def head_bucket(self, Bucket):
                self.bucket = Bucket
            def head_object(self, Bucket, Key):
                if Key not in self.objects:
                    raise ClientError({'Error': {'Code': '404'}, 'ResponseMetadata': {'HTTPStatusCode':404}}, 'HeadObject')
                obj = self.objects[Key]
                return {'Metadata': obj['Metadata'], 'ContentLength':len(obj['Body'])}
            def put_object(self, Bucket, Key, Body, ContentType, Metadata, IfNoneMatch):
                if Key in self.objects: raise AssertionError('overwrite')
                self.objects[Key] = {'Body':Body, 'Metadata':Metadata}; self.writes += 1
            def get_object(self, Bucket, Key):
                return {'Body':io.BytesIO(self.objects[Key]['Body'])}

        cloud = FakeCloud()
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            with (base/'products.csv').open('w',encoding='utf-8',newline='') as f:
                w = csv.writer(f);w.writerow(['image number','product name','category','brand','pack quantity'])
                w.writerow(['7','Gel Pen','Pens','Test Brand','Pack of 5'])
            with zipfile.ZipFile(base/'images.zip','w') as z:
                z.writestr('0007.jpg',jpeg(1))
            kwargs = dict(csv_path=str(base/'products.csv'), images=str(base/'images.zip'),
                          report_dir=str(base/'reports'))
            with override_settings(DEBUG=False, STUDENTSTORE_MEDIA_PROVIDER='r2',
                                   AWS_STORAGE_BUCKET_NAME='ojasone-studentstore',
                                   AWS_ACCESS_KEY_ID='test', AWS_SECRET_ACCESS_KEY='test',
                                   AWS_S3_ENDPOINT_URL='https://account.r2.cloudflarestorage.com'):
                call_command('import_ojas_batch02', dry_run=True, stdout=io.StringIO(), **kwargs)
                self.assertEqual(Product.objects.count(), 0)
                approval = next((base/'reports').glob('*.json'))
                wrong = base/'wrong.json';wrong.write_text('{"mode":"dry-run"}',encoding='utf-8')
                with patch('catalog.management.commands.import_ojas_batch02.verify_production'), \
                     patch('catalog.management.commands.import_ojas_batch02.make_r2_client',return_value=(cloud,'ojasone-studentstore')):
                    with self.assertRaises(Exception):
                        call_command('import_ojas_batch02', commit=True, approved_dry_run=str(wrong),
                                     stdout=io.StringIO(), **kwargs)
                    self.assertEqual(Product.objects.count(), 0)
                    call_command('import_ojas_batch02', commit=True, approved_dry_run=str(approval),
                                 stdout=io.StringIO(), **kwargs)
                    self.assertEqual(Product.objects.count(), 1)
                    item = Product.objects.get(sku='OJAS-B02-0007')
                    self.assertEqual(item.images.first().image.name, 'products/batch-02/0007.jpg')
                    self.assertTrue(item.is_active)
                    self.assertEqual(cloud.writes, 1)
                    call_command('import_ojas_batch02', commit=True, approved_dry_run=str(approval),
                                 stdout=io.StringIO(), **kwargs)
                    self.assertEqual(cloud.writes, 1)
                    self.assertEqual(Product.objects.count(), 1)

class ExistingMediaSyncTests(TestCase):
    """Legacy product and banner images remain same DB names after R2 upload."""

    def test_sync_product_and_banner_keeps_existing_records(self):
        import tempfile
        from pathlib import Path
        from banners.models import Banner
        from unittest.mock import MagicMock, patch
        from catalog.models import ProductImage
        category=Category.objects.create(name='Existing',slug='existing')
        item=Product.objects.create(name='Legacy Item',sku='LEG-1',slug='leg-1',
                                    category=category,price=Decimal('30.00'),stock=5)
        photo=ProductImage.objects.create(product=item,image='products/2026/01/legacy.jpg')
        banner=Banner.objects.create(title='Old banner',image='banners/2026/01/banner.jpg',is_active=True)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for key in (photo.image.name,banner.image.name):
                loc=root/key;loc.parent.mkdir(parents=True,exist_ok=True);loc.write_bytes(jpeg(1))
            with override_settings(MEDIA_ROOT=root, STUDENTSTORE_MEDIA_PROVIDER='r2',DEBUG=False):
                with patch('catalog.management.commands.sync_existing_media_to_r2.verify_production'), \
                     patch('catalog.management.commands.sync_existing_media_to_r2.make_r2_client',return_value=(MagicMock(),'ojasone-studentstore')), \
                     patch('catalog.management.commands.sync_existing_media_to_r2.put_r2_verified',return_value='uploaded') as put:
                    call_command('sync_existing_media_to_r2',dry_run=True,legacy_only=True,
                                 report_dir=str(root/'reports'),stdout=io.StringIO())
                    self.assertEqual(put.call_count,0)
                    call_command('sync_existing_media_to_r2',commit=True,legacy_only=True,
                                 report_dir=str(root/'reports'),stdout=io.StringIO())
                    self.assertEqual(put.call_count,2)
                    self.assertEqual({c.args[2] for c in put.call_args_list},
                                     {'products/2026/01/legacy.jpg','banners/2026/01/banner.jpg'})
        photo.refresh_from_db();banner.refresh_from_db();item.refresh_from_db()
        self.assertEqual(photo.image.name,'products/2026/01/legacy.jpg')
        self.assertEqual(banner.image.name,'banners/2026/01/banner.jpg')
        self.assertEqual((item.stock,item.price),(5,Decimal('30.00')))


class RealOjasCsvHeaderRegressionTests(TestCase):
    """These headers are taken from the user's actual Batch-02 CSV validation log."""

    HEADERS = [
        'Photo No', 'Image Filename', 'Brand', 'Exact Google Image Search Phrase',
        'Proposed Product Title', 'Department', 'Category', 'Subcategory',
        'Pack / Variant To Find', 'Expected Contents (verify)', 'Image Provided?',
        'Exact Model / Barcode (fill if known)', 'Packaging Quantity Verified?',
        'Manufacturer MRP (₹)', 'Selling Price (₹)',
        'Physical Stock (saleable packs)', 'Product Status', 'Notes',
    ]

    def test_headers_and_unverified_variant_are_recognised(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'OJAS_ONE_2000_updated_list.csv'
            with path.open('w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.HEADERS)
                writer.writerow([
                    '0007', '0007.jpg', 'Cello', 'cell pen', 'Gel Pen',
                    'Stationery', 'Pens', 'Writing Pens', 'Pack of 5',
                    '5 pens (verify)', 'Yes', '', 'No', '100', '85',
                    '', 'Review', '',
                ])
            rows = read_rows(path)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row['serial'], '0007')
            self.assertEqual(row['image_file'], '0007.jpg')
            self.assertEqual(row['name'], 'Gel Pen')
            self.assertEqual(row['category'], 'Pens')
            self.assertEqual(row['subcategory'], 'Writing Pens')
            self.assertEqual(row['brand'], 'Cello')
            self.assertEqual(row['pack'], 'Pack of 5')
            self.assertEqual(row['mrp'], '100')
            self.assertEqual(row['selling'], '85')
            self.assertTrue(row['pack_unverified_source'])

    def test_real_headers_support_read_only_import_dry_run(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_csv = root / 'OJAS_ONE_2000_updated_list.csv'
            source_zip = root / 'OJAS_ONE_2000_images.zip'
            with source_csv.open('w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.HEADERS)
                writer.writerow([
                    '7', '0007.jpg', 'Cello', 'gel pen', 'Gel Pen',
                    'Stationery', 'Pens', 'Writing Pens', 'Pack of 5',
                    'verify the quantity', 'Yes', '', '', '', '',
                    '', 'Needs review', '',
                ])
            with zipfile.ZipFile(source_zip, 'w') as images:
                images.writestr('images/0007.jpg', jpeg(1))
            with override_settings(DEBUG=True, STUDENTSTORE_MEDIA_PROVIDER='local'):
                call_command(
                    'import_ojas_batch02', csv_path=str(source_csv),
                    images=str(source_zip), dry_run=True,
                    report_dir=str(root / 'reports'),
                    stdout=io.StringIO(), stderr=io.StringIO(),
                )
            self.assertEqual(Product.objects.count(), 0)
            data = json.loads(next((root / 'reports').glob('*.json')).read_text(encoding='utf-8'))
            self.assertEqual(data['counts'].get('ready_dry_run'), 1)
            record = data['records'][0]
            self.assertEqual(record['sku'], 'OJAS-B02-0007')
            self.assertIn('unverified pack quantity / CSV variant', record['requires_review'])
            self.assertTrue(12 <= record['estimated_stock'] <= 40)
