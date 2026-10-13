"""Read-only deployment configuration check (no network calls)."""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Validate production settings without contacting external services.'

    def handle(self, *args, **options):
        if settings.DEBUG:
            raise CommandError('DEBUG must be False in production.')
        if not settings.ALLOWED_HOSTS or '*' in settings.ALLOWED_HOSTS:
            raise CommandError('Set explicit production ALLOWED_HOSTS.')
        if settings.STUDENTSTORE_MEDIA_PROVIDER != 'r2':
            raise CommandError('Configure durable R2 media storage for production.')
        # Remaining checks apply only to actual production settings, not local test overrides.
        if (getattr(settings, 'SETTINGS_MODULE', None) or '').endswith('.production'):
            if len(settings.SECRET_KEY) < 40:
                raise CommandError('Use a strong DJANGO_SECRET_KEY of at least 40 characters.')
            if not settings.SECURE_SSL_REDIRECT or not settings.CSRF_COOKIE_SECURE or not settings.SESSION_COOKIE_SECURE:
                raise CommandError('Secure HTTPS redirect and cookies are required.')
            if not settings.DATABASES['default'].get('PASSWORD'):
                raise CommandError('Database password is missing.')
            for name in ('AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_STORAGE_BUCKET_NAME', 'AWS_S3_ENDPOINT_URL', 'AWS_S3_CUSTOM_DOMAIN'):
                if not getattr(settings, name, ''):
                    raise CommandError(f'Missing R2 setting: {name}')
        self.stdout.write(self.style.SUCCESS('Deployment configuration checks passed.'))
