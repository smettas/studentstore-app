"""Regression: Django's SETTINGS_MODULE can be None during tests."""
from io import StringIO
from django.core.management import call_command
from django.test import SimpleTestCase, override_settings


class DeploymentCommandRegressionTests(SimpleTestCase):
    @override_settings(DEBUG=False, ALLOWED_HOSTS=['example.com'], STUDENTSTORE_MEDIA_PROVIDER='r2', SETTINGS_MODULE=None)
    def test_none_settings_module_does_not_crash(self):
        output = StringIO()
        call_command('deployment_check', stdout=output)
        self.assertIn('passed', output.getvalue())
