import unittest
from services.runtime_secrets import resolve_flask_secret, require_jwt_secret


class RuntimeSecretsTest(unittest.TestCase):
    def test_missing_secret_is_random_and_not_shared(self):
        first = resolve_flask_secret(None)
        second = resolve_flask_secret('')
        self.assertEqual(len(first), 64)
        self.assertNotEqual(first, second)

    def test_explicit_secret_is_preserved(self):
        self.assertEqual(resolve_flask_secret('configured-test-value'), 'configured-test-value')

    def test_old_placeholder_is_rejected(self):
        for value in ['your-secret-key-here', 'change-me-to-a-random-secret']:
            with self.assertRaisesRegex(ValueError, 'SECRET_KEY'):
                resolve_flask_secret(value)

    def test_jwt_requires_an_explicit_value(self):
        for value in [None, '', '  ']:
            with self.assertRaisesRegex(ValueError, 'JWT_SECRET'):
                require_jwt_secret(value)

    def test_jwt_rejects_the_old_example(self):
        with self.assertRaisesRegex(ValueError, 'JWT_SECRET'):
            require_jwt_secret('change-me-to-a-random-jwt-secret')

    def test_jwt_preserves_a_configured_value(self):
        self.assertEqual(require_jwt_secret('test-secret-key-for-testing'), 'test-secret-key-for-testing')
