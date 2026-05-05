import importlib
import os
import unittest

from agenticbrainrot.utils.rollbar_utils import transform_rollbar_payload

# Load production settings directly without going through Django's settings proxy,
# since pytest-django already configures Django with test settings before this runs.
os.environ.setdefault('DJANGO_SECRET_KEY', 'test-secret-key-123')
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
os.environ.setdefault('ROLLBAR_ENABLED', 'True')
os.environ.setdefault('ROLLBAR_ACCESS_TOKEN', 'test-token')


_prod = importlib.import_module('config.settings.production')


class ProductionSettingsTest(unittest.TestCase):
    def test_huey_config(self):
        """Verify HUEY configuration is correct and doesn't cause over-determined error."""
        huey_config = _prod.HUEY
        self.assertEqual(huey_config['huey_class'], 'huey.RedisHuey')
        self.assertEqual(huey_config['url'], os.environ['REDIS_URL'])
        self.assertNotIn('consumer_options', huey_config)

        from huey import RedisHuey
        try:
            h = RedisHuey(huey_config['name'], url=huey_config['url'], immediate=huey_config['immediate'])
            self.assertIsInstance(h, RedisHuey)
        except Exception as e:
            self.fail(f"RedisHuey instantiation failed: {e}")

    def test_rollbar_config(self):
        """Verify ROLLBAR settings are correctly applied."""
        self.assertTrue(_prod.ROLLBAR_ENABLED)
        rb = _prod.ROLLBAR
        self.assertEqual(rb['access_token'], 'test-token')
        self.assertEqual(rb['transform'], 'agenticbrainrot.utils.rollbar_utils.transform_rollbar_payload')
        self.assertTrue(rb['suppress_re_reporting'])
        self.assertTrue(rb['locals']['enabled'])

        filters = dict(rb['exception_level_filters'])
        self.assertEqual(filters.get('django.http.Http404'), 'ignored')
        self.assertEqual(filters.get('django.core.exceptions.PermissionDenied'), 'ignored')

    def test_rollbar_transform_payload(self):
        """Verify the custom rollbar transform function works."""
        test_payload = {
            'body': {
                'trace': {
                    'exception': {
                        'class': 'ConnectionError'
                    }
                }
            }
        }
        transformed = transform_rollbar_payload(test_payload)
        self.assertIn('fingerprint', transformed)

        fp1 = transform_rollbar_payload(test_payload)['fingerprint']
        fp2 = transform_rollbar_payload(test_payload)['fingerprint']
        self.assertEqual(fp1, fp2)

        normal_payload = {
            'body': {
                'trace': {
                    'exception': {
                        'class': 'ValueError'
                    }
                }
            }
        }
        transformed_normal = transform_rollbar_payload(normal_payload)
        self.assertNotIn('fingerprint', transformed_normal)

    def test_logging_config(self):
        """Verify mail_admins is removed from logging."""
        logging_config = _prod.LOGGING
        handlers = logging_config.get('handlers', {})
        self.assertNotIn('mail_admins', handlers)

        django_request = logging_config.get('loggers', {}).get('django.request', {})
        self.assertNotIn('mail_admins', django_request.get('handlers', []))
        self.assertIn('console', django_request.get('handlers', []))
