"""Stdlib-only offline tests; no Django or database connection required."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import release_readiness


class ReleaseReadinessTests(unittest.TestCase):
    def test_railway_json_matches_health_endpoint(self):
        self.assertEqual(release_readiness.check_railway(), [])

    def test_required_release_files_exist(self):
        self.assertEqual(release_readiness.check_files(), [])

    def test_invalid_railway_json_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            (temp / 'railway.json').write_text('{invalid', encoding='utf-8')
            with patch.object(release_readiness, 'ROOT', temp):
                self.assertTrue(release_readiness.check_railway())

    def test_manual_checks_are_not_silently_approved(self):
        # A passing offline inspection must not claim the production launch is approved.
        import inspect
        source = inspect.getsource(release_readiness.main)
        self.assertIn('Launch approval: NOT GRANTED', source)


if __name__ == '__main__':
    unittest.main()
