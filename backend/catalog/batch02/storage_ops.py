"""Content-verified, non-overwriting object saves for local storage or R2."""
import hashlib
import os
from pathlib import Path
from urllib.parse import urlparse


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def digest_stream(stream):
    h = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        h.update(block)
    return h.hexdigest()


def object_matches(storage, key, data):
    if not storage.exists(key):
        return False
    with storage.open(key, 'rb') as stream:
        return digest_stream(stream) == digest_bytes(data)


def save_verified(storage, key, data):
    """Never overwrite a different existing object. Reuse identical upload on reruns.

    Returns 'reused' or 'uploaded'. A failed database save may leave an unreferenced
    object which a safe rerun reuses; this is intentionally preferable to deletion.
    """
    from django.core.files.base import ContentFile
    if storage.exists(key):
        if object_matches(storage, key, data):
            return 'reused'
        raise ValueError('Storage key collision: existing object has DIFFERENT image bytes; no overwrite')
    saved = storage.save(key, ContentFile(data, name=Path(key).name))
    if saved != key:
        # Django may rename a key due to concurrent writes. Do not link that object.
        # Leave orphan for operator inspection rather than deleting anything shared.
        raise ValueError(f'Storage renamed object to {saved!r}; intended key is unavailable')
    if not object_matches(storage, key, data):
        raise ValueError('Uploaded image did not pass read-after-write SHA256 verification')
    return 'uploaded'


def make_r2_client():
    """Independent client: staging uploads works even when default Django storage is local."""
    import boto3
    from botocore.config import Config
    required = ('R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_BUCKET_NAME')
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise ValueError('Missing Student Store R2 configuration: ' + ', '.join(missing))
    account = os.environ.get('R2_ACCOUNT_ID', '').strip()
    if account and (len(account) != 32 or not all(c in '0123456789abcdefABCDEF' for c in account)):
        raise ValueError('R2_ACCOUNT_ID must be the 32-character Cloudflare account identifier')
    endpoint = os.environ.get('R2_ENDPOINT_URL', '').strip() or (
        f'https://{account}.r2.cloudflarestorage.com' if account else ''
    )
    if account and endpoint and urlparse(endpoint).hostname != f'{account}.r2.cloudflarestorage.com':
        raise ValueError('R2_ACCOUNT_ID and R2_ENDPOINT_URL refer to different accounts')
    if urlparse(endpoint).scheme != 'https' or not urlparse(endpoint).hostname:
        raise ValueError('R2_ENDPOINT_URL must be a valid HTTPS endpoint')
    client = boto3.client('s3', endpoint_url=endpoint,
        aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
        region_name='auto', config=Config(signature_version='s3v4', s3={'addressing_style': 'path'}))
    return client, os.environ['R2_BUCKET_NAME']


def r2_has_matching(client, bucket, key, data):
    """No assumptions about ETags (multipart ETags are not content hashes)."""
    from botocore.exceptions import ClientError
    try:
        head = client.head_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        if exc.response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 404 or \
           exc.response.get('Error', {}).get('Code') in ('404', 'NoSuchKey', 'NotFound'):
            return False
        raise
    digest = digest_bytes(data)
    if head.get('Metadata', {}).get('sha256') == digest and head.get('ContentLength') == len(data):
        return True
    # Verify existing objects lacking our SHA256 metadata without overwriting them.
    stream = client.get_object(Bucket=bucket, Key=key)['Body']
    try:
        return digest_stream(stream) == digest
    finally:
        stream.close()


def put_r2_verified(client, bucket, key, data, content_type='image/jpeg'):
    from botocore.exceptions import ClientError
    if r2_exists(client, bucket, key):
        if r2_has_matching(client, bucket, key, data):
            return 'reused'
        raise ValueError('R2 key collision: unrelated object exists; refusing overwrite')
    try:
        client.put_object(Bucket=bucket, Key=key, Body=data,
            ContentType=content_type, Metadata={'sha256': digest_bytes(data)}, IfNoneMatch='*')
    except ClientError as exc:
        if exc.response.get('ResponseMetadata', {}).get('HTTPStatusCode') in (409, 412):
            if r2_has_matching(client, bucket, key, data):
                return 'reused'
            raise ValueError('R2 concurrent object collision; refusing overwrite') from exc
        raise
    if not r2_has_matching(client, bucket, key, data):
        raise ValueError('R2 object failed read-after-upload SHA256 verification')
    return 'uploaded'


def r2_exists(client, bucket, key):
    from botocore.exceptions import ClientError
    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as exc:
        code = exc.response.get('Error', {}).get('Code')
        status = exc.response.get('ResponseMetadata', {}).get('HTTPStatusCode')
        if code in ('404', 'NoSuchKey', 'NotFound') or status == 404:
            return False
        raise


def source_fingerprint(path):
    """Source contents manifest to prevent approval of a different image ZIP/folder.

    ZIP files are hashed byte-for-byte. Directories use relative paths, lengths,
    modification times and contents for each numbered image, deterministic order.
    This does not modify any file.
    """
    from catalog.batch02.sources import EXTENSIONS
    target = Path(path)
    if target.is_file():
        with target.open('rb') as stream:
            return digest_stream(stream)
    if not target.is_dir():
        raise ValueError('Image source missing')
    h = hashlib.sha256()
    for item in sorted((p for p in target.rglob('*') if p.is_file() and p.suffix.lower() in EXTENSIONS),
                       key=lambda x: str(x.relative_to(target)).casefold()):
        rel = str(item.relative_to(target)).replace('\\', '/')
        h.update(rel.encode('utf-8'))
        h.update(b'\0')
        h.update(str(item.stat().st_size).encode())
        with item.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(block)
    return h.hexdigest()
