"""Preserve existing product/banner media when moving local PostgreSQL to Railway.

Uploads media referenced by the remote database under their ORIGINAL object keys,
so ProductImage and Banner rows remain unchanged. No local file is deleted.
"""
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from catalog.batch02.guards import EXPECTED_BUCKET, db_identity, verify_production
from catalog.batch02.storage_ops import make_r2_client, put_r2_verified
from catalog.models import ProductImage
from banners.models import Banner


class Command(BaseCommand):
    help = "Read LOCAL existing product/banner media and upload byte-for-byte to private R2."

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument('--dry-run', action='store_true')
        mode.add_argument('--commit', action='store_true')
        parser.add_argument('--legacy-only', action='store_true', help='Skip already imported Batch-02 images')
        parser.add_argument('--report-dir', default='batch02_reports')
        parser.add_argument('--production-ack')
        parser.add_argument('--confirm-db-fingerprint')
        parser.add_argument('--backup-file')

    def handle(self, *args, **options):
        commit = options['commit']
        if commit:
            verify_production(options)
            try:
                client, bucket = make_r2_client()
                if bucket != EXPECTED_BUCKET:
                    raise CommandError('Wrong bucket: refusing to use Academy storage.')
                client.head_bucket(Bucket=bucket)
            except CommandError:
                raise
            except Exception as exc:
                raise CommandError(f'R2 connectivity failed ({type(exc).__name__}).') from None
        else:
            client, bucket = None, None
        items = []
        for photo in ProductImage.objects.select_related('product').order_by('id'):
            if options['legacy_only'] and photo.product.sku.startswith('OJAS-B02-'):
                continue
            items.append(('product', photo.pk, photo.product.sku, photo.image.name))
        for banner in Banner.objects.order_by('id'):
            items.append(('banner', banner.pk, '', banner.image.name))

        root = Path(settings.MEDIA_ROOT).resolve()
        counts, records = Counter(), []
        for kind, pk, sku, key in items:
            status, detail = 'missing', 'Local photo not found'
            try:
                if (not key or len(key)>350 or '\\' in key or '..' in key.split('/') or
                    not key.startswith('products/' if kind == 'product' else 'banners/')):
                    raise ValueError('Unsafe/unexpected media key')
                local_path = (root / key).resolve()
                if not local_path.is_relative_to(root):
                    raise ValueError('Local media path escapes root')
                if not local_path.is_file():
                    status, detail = 'missing', 'Local photo not found (restore from local backup)'
                elif local_path.stat().st_size > 20 * 1024 * 1024:
                    status, detail = 'failed', 'Image larger than 20 MB'
                else:
                    from PIL import Image
                    import io
                    import mimetypes
                    data = local_path.read_bytes()
                    with Image.open(io.BytesIO(data)) as im: im.verify()
                    if commit:
                        action = put_r2_verified(client,bucket,key,data,mimetypes.guess_type(key)[0] or 'application/octet-stream')
                        status, detail = action, 'R2 content hash verified. Existing DB reference unchanged.'
                    else:
                        status, detail = 'ready_dry_run', 'Local media exists; no R2 operations performed.'
            except Exception as exc:
                status, detail = 'failed', f'{type(exc).__name__}; inspect local media privately'
            counts[status] += 1
            records.append({'kind':kind, 'id':pk, 'sku':sku, 'key':key, 'status':status, 'detail':detail})
        report_dir=Path(options['report_dir'])
        report_dir.mkdir(parents=True,exist_ok=True)
        name = report_dir / ('existing_media_r2_'+('commit_' if commit else 'dryrun_')+
                              datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        summary={'mode':'commit' if commit else 'dry-run','db_fingerprint':db_identity()['fingerprint'],
                 'total':len(items),'counts':dict(counts),'records':records,
                 'disclaimer':'NO database rows or local photos were modified. Review missing files.'}
        name.with_suffix('.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
        with name.with_suffix('.csv').open('w',newline='',encoding='utf-8-sig') as stream:
            writer=csv.DictWriter(stream,fieldnames=('kind','id','sku','key','status','detail'))
            writer.writeheader();writer.writerows(records)
        self.stdout.write(f'Existing media sync {summary["mode"]}: {dict(counts)}; DB untouched')
        self.stdout.write('Reports: '+str(name)+'.json/.csv')
