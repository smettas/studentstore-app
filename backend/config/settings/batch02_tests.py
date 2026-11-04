"""Test-only SQLite configuration. NEVER use for production or actual imports."""
import os
os.environ.setdefault('DJANGO_SECRET_KEY', 'batch02-test-only-secret-not-for-any-runtime-1234567890')
from .local import *  # noqa: F401,F403
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
STUDENTSTORE_MEDIA_PROVIDER = 'local'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
