from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parents[2]
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "accounts",
    "catalog",
    "cart",
    "wishlist",
    "addresses",
    "orders",
    "payments",
    "coupons",
    "banners",
    "notifications",
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="studentstore"),
        "USER": env("POSTGRES_USER", default="studentstore_user"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="change-me"),
        "HOST": env("POSTGRES_HOST", default="127.0.0.1"),
        "PORT": env("POSTGRES_PORT", default="5432"),
        "CONN_MAX_AGE": env.int("POSTGRES_CONN_MAX_AGE", default=60),
    }
}

LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Phase 12: public product/banner media only. Static assets stay on WhiteNoise.
# Use local files until Cloudflare R2 is configured. No credentials in source.
STUDENTSTORE_MEDIA_PROVIDER = env("STUDENTSTORE_MEDIA_PROVIDER", default="local").lower()
if STUDENTSTORE_MEDIA_PROVIDER not in {"local", "r2"}:
    raise ValueError("STUDENTSTORE_MEDIA_PROVIDER must be 'local' or 'r2'")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
if STUDENTSTORE_MEDIA_PROVIDER == "r2":
    AWS_ACCESS_KEY_ID = env("R2_ACCESS_KEY_ID", default="")
    AWS_SECRET_ACCESS_KEY = env("R2_SECRET_ACCESS_KEY", default="")
    AWS_STORAGE_BUCKET_NAME = env("R2_BUCKET_NAME", default="")
    AWS_S3_ENDPOINT_URL = env("R2_ENDPOINT_URL", default="")
    AWS_S3_CUSTOM_DOMAIN = env("R2_PUBLIC_DOMAIN", default="")
    AWS_S3_REGION_NAME = "auto"
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False
    AWS_S3_ADDRESSING_STYLE = "path"
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "public, max-age=86400"}
    STORAGES["default"] = {"BACKEND": "core.storage.backends.PublicProductMediaStorage"}


AUTH_USER_MODEL = "accounts.User"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_THROTTLE_RATES": {"otp_request": "5/hour", "otp_verify": "15/hour"},
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

OTP_PROVIDER = env("OTP_PROVIDER", default="console")
MSG91_AUTH_KEY = env("MSG91_AUTH_KEY", default="")
MSG91_TEMPLATE_ID = env("MSG91_TEMPLATE_ID", default="")

# Shipping configuration (INR). Override in backend/.env.
STUDENTSTORE_DELIVERY_FEE = env("STUDENTSTORE_DELIVERY_FEE", default="40.00")
STUDENTSTORE_FREE_DELIVERY_THRESHOLD = env("STUDENTSTORE_FREE_DELIVERY_THRESHOLD", default="999.00")

# Razorpay test credentials for local development; use live credentials only after verification.
RAZORPAY_KEY_ID = env("RAZORPAY_KEY_ID", default="")
RAZORPAY_KEY_SECRET = env("RAZORPAY_KEY_SECRET", default="")
RAZORPAY_WEBHOOK_SECRET = env("RAZORPAY_WEBHOOK_SECRET", default="")
