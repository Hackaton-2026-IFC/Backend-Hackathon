import os
from unittest.mock import Mock, patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from core.models.google_identity import GoogleIdentity

User = get_user_model()

class GoogleAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.env = patch.dict(os.environ, {'GOOGLE_CLIENT_ID': 'test-client'})
        self.env.start()
        self.addCleanup(self.env.stop)

    @patch('core.views.google_auth.requests.get')
    def test_create_and_login_google(self, mocked):
        mocked.return_value = Mock(status_code=200, json=lambda: {
            'sub': 'google-123', 'email': 'novo@google.com', 'name': 'Novo',
            'aud': 'test-client', 'iss': 'accounts.google.com', 'email_verified': 'true',
        })
        first = self.client.post('/api/auth/google/', {'credential': 'valid'}, format='json')
        self.assertEqual(first.status_code, 200)
        self.assertIn('access', first.data)
        second = self.client.post('/api/auth/google/', {'credential': 'valid'}, format='json')
        self.assertEqual(second.status_code, 200)
        self.assertEqual(GoogleIdentity.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)

    @patch('core.views.google_auth.requests.get')
    def test_does_not_takeover_existing_email(self, mocked):
        User.objects.create_user(email='novo@google.com', password='senha123')
        mocked.return_value = Mock(status_code=200, json=lambda: {
            'sub': 'google-123', 'email': 'novo@google.com', 'aud': 'test-client',
            'iss': 'accounts.google.com', 'email_verified': 'true',
        })
        resp = self.client.post('/api/auth/google/', {'credential': 'valid'}, format='json')
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(GoogleIdentity.objects.count(), 0)

    @patch('core.views.google_auth.requests.get')
    def test_reject_wrong_audience(self, mocked):
        mocked.return_value = Mock(status_code=200, json=lambda: {
            'sub': 'google-123', 'email': 'novo@google.com', 'aud': 'other-app',
            'iss': 'accounts.google.com', 'email_verified': 'true',
        })
        self.assertEqual(self.client.post('/api/auth/google/', {'credential':'x'}, format='json').status_code, 400)
