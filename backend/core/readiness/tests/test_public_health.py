"""API liveness checks: no database or external services required."""
from django.test import SimpleTestCase
from django.urls import reverse


class PublicHealthTests(SimpleTestCase):
    def test_health_returns_json(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')

    def test_health_is_read_only(self):
        self.assertEqual(self.client.post('/api/health/').status_code, 405)

    def test_health_has_no_sensitive_information(self):
        body = self.client.get('/api/health/').json()
        for key in ('database_url', 'secret_key', 'password', 'token'):
            self.assertNotIn(key, body)
