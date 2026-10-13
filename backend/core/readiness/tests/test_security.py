"""Read-only checks of deployment security invariants (no DB required)."""
from django.conf import settings
from django.test import SimpleTestCase, override_settings
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO


class ProductionGuardTests(SimpleTestCase):
    @override_settings(DEBUG=True, ALLOWED_HOSTS=['example.com'], STUDENTSTORE_MEDIA_PROVIDER='r2')
    def test_deployment_check_rejects_debug(self):
        with self.assertRaises(CommandError):
            call_command('deployment_check', stdout=StringIO())

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['*'], STUDENTSTORE_MEDIA_PROVIDER='r2')
    def test_deployment_check_rejects_wildcard_hosts(self):
        with self.assertRaises(CommandError):
            call_command('deployment_check', stdout=StringIO())

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['example.com'], STUDENTSTORE_MEDIA_PROVIDER='local')
    def test_deployment_check_rejects_ephemeral_media(self):
        with self.assertRaises(CommandError):
            call_command('deployment_check', stdout=StringIO())

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['example.com'], STUDENTSTORE_MEDIA_PROVIDER='r2')
    def test_deployment_check_accepts_configured_guardrails(self):
        output = StringIO()
        call_command('deployment_check', stdout=output)
        self.assertIn('passed', output.getvalue())
