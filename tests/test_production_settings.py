import os
import unittest
# Set environment variables BEFORE importing django or settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
os.environ['DJANGO_SECRET_KEY'] = 'test-secret-key-123'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
os.environ['ROLLBAR_ENABLED'] = 'True'
os.environ['ROLLBAR_ACCESS_TOKEN'] = 'test-token'

import django
from django.conf import settings
from agenticbrainrot.utils.rollbar_utils import transform_rollbar_payload

class ProductionSettingsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize Django with production settings
        if not settings.configured:
            django.setup()

    def test_huey_config(self):
        """Verify HUEY configuration is correct and doesn't cause over-determined error."""
        huey_config = settings.HUEY
        self.assertEqual(huey_config['huey_class'], 'huey.RedisHuey')
        self.assertEqual(huey_config['url'], os.environ['REDIS_URL'])
        # Ensure consumer_options is NOT in the config (the fix)
        self.assertNotIn('consumer_options', huey_config)

        # Verify we can actually instantiate the class if huey is installed
        from huey import RedisHuey
        try:
            # We don't want to actually connect to Redis, just check if constructor works
            # RedisHuey calls create_storage in __init__ which might fail if config is bad
            h = RedisHuey(huey_config['name'], url=huey_config['url'], immediate=huey_config['immediate'])
            self.assertIsInstance(h, RedisHuey)
        except Exception as e:
            self.fail(f"RedisHuey instantiation failed: {e}")

    def test_rollbar_config(self):
        """Verify ROLLBAR settings are correctly applied."""
        self.assertTrue(settings.ROLLBAR_ENABLED)
        rb = settings.ROLLBAR
        self.assertEqual(rb['access_token'], 'test-token')
        self.assertEqual(rb['transform'], 'agenticbrainrot.utils.rollbar_utils.transform_rollbar_payload')
        self.assertTrue(rb['suppress_re_reporting'])
        self.assertTrue(rb['locals']['enabled'])

        # Verify exception filters
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

        # Test consistency
        fp1 = transform_rollbar_payload(test_payload)['fingerprint']
        fp2 = transform_rollbar_payload(test_payload)['fingerprint']
        self.assertEqual(fp1, fp2)

        # Different class should have different or no fingerprint (unless noisy)
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
        logging_config = settings.LOGGING
        handlers = logging_config.get('handlers', {})
        self.assertNotIn('mail_admins', handlers)

        django_request = logging_config.get('loggers', {}).get('django.request', {})
        self.assertNotIn('mail_admins', django_request.get('handlers', []))
        self.assertIn('console', django_request.get('handlers', []))
