"""Nonsecret, reproducible target identity and production import safety checks."""
import hashlib
from datetime import timedelta
from pathlib import Path
from django.conf import settings
from django.core.management.base import CommandError
from django.db import connection
from django.utils import timezone

EXPECTED_BUCKET = "ojasone-studentstore"
ACK = "IMPORT-OJAS-B02-TO-RAILWAY"


def db_identity():
    """Values deliberately exclude password/credentials, URL and secret tokens."""
    db = connection.settings_dict
    parts = [str(db.get(x) or "") for x in ("ENGINE", "HOST", "PORT", "NAME", "USER")]
    return {
        "engine": parts[0], "host": parts[1], "port": parts[2],
        "database": parts[3], "user": parts[4],
        "fingerprint": hashlib.sha256("\0".join(parts).encode()).hexdigest()[:20],
    }


def verify_production(options):
    if settings.DEBUG or getattr(settings, "STUDENTSTORE_MEDIA_PROVIDER", "local") != "r2":
        raise CommandError("Production commit requires production settings, DEBUG=False and R2 media.")
    if options.get("production_ack") != ACK:
        raise CommandError("Production acknowledgment missing: --production-ack " + ACK)
    if getattr(settings, "AWS_STORAGE_BUCKET_NAME", "") != EXPECTED_BUCKET:
        raise CommandError("Wrong R2 bucket; refusing to touch the Academy bucket.")
    identity = db_identity()
    if "postgresql" not in identity["engine"]:
        raise CommandError("Production import must use PostgreSQL.")
    if identity["host"].lower() in {"localhost", "127.0.0.1", "", "::1"}:
        raise CommandError("Refusing production import to localhost; connect to Railway Student Store DB.")
    if identity["fingerprint"] != options.get("confirm_db_fingerprint"):
        raise CommandError("Database fingerprint mismatch; run inspect_studentstore_target and confirm exact target.")
    backup_name = options.get("backup_file")
    if not backup_name:
        raise CommandError("A verified recent DB backup is required: --backup-file <filename>.")
    backup = Path(backup_name)
    if not backup.is_file() or backup.stat().st_size < 512:
        raise CommandError("Database backup file is absent/empty; no import performed.")
    from datetime import datetime, timezone as tz
    changed = datetime.fromtimestamp(backup.stat().st_mtime, tz=tz.utc)
    if timezone.now() - changed > timedelta(hours=48):
        raise CommandError("Backup is over 48 hours old; take a new DB backup.")
    return identity
