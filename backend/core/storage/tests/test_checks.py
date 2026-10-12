"""Unit checks that do not connect to PostgreSQL or Cloudflare."""
from django.test import SimpleTestCase, override_settings

from core.storage.checks import check_product_media_storage


class MediaStorageConfigurationTests(SimpleTestCase):
    @override_settings(DEBUG=True, STUDENTSTORE_MEDIA_PROVIDER="local")
    def test_local_media_allowed_during_development(self):
        self.assertEqual(check_product_media_storage(None), [])

    @override_settings(
        DEBUG=True, STUDENTSTORE_MEDIA_PROVIDER="r2",
        AWS_ACCESS_KEY_ID="", AWS_SECRET_ACCESS_KEY="",
        AWS_STORAGE_BUCKET_NAME="", AWS_S3_ENDPOINT_URL="",
        AWS_S3_CUSTOM_DOMAIN="",
    )
    def test_r2_missing_credentials_is_rejected(self):
        issues = check_product_media_storage(None)
        self.assertTrue(any(issue.id == "studentstore.E1202" for issue in issues))

    @override_settings(
        DEBUG=True, STUDENTSTORE_MEDIA_PROVIDER="r2",
        AWS_ACCESS_KEY_ID="test", AWS_SECRET_ACCESS_KEY="test",
        AWS_STORAGE_BUCKET_NAME="test", AWS_S3_ENDPOINT_URL="http://bad",
        AWS_S3_CUSTOM_DOMAIN="https://images.example.com",
    )
    def test_invalid_public_hostname_and_endpoint_rejected(self):
        issues = check_product_media_storage(None)
        self.assertTrue(any(issue.id == "studentstore.E1203" for issue in issues))
        self.assertTrue(any(issue.id == "studentstore.E1204" for issue in issues))
