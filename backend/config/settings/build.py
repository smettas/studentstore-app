"""Build-time settings only for collectstatic; never run the web server with these."""
import os

os.environ.setdefault("DJANGO_SECRET_KEY", "build-only-placeholder-not-for-runtime-000000000000000000")
from .base import *  # noqa: F401,F403

DEBUG = False
