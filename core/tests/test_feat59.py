import os
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient


User = get_user_model()


class GooglePhotoTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.payload = {
            'aud': 'test-google-client',
            'iss': 'https://accounts.google.com',
            'email_verified': 'true',
            'sub': 'google-user-photo-001',
            'email': 'photo-google@test.com',
            'name': 'Google Test User',
            'picture': 'https://lh3.googleusercontent.com/a/photo123',
        }

    @patch.dict(os.environ, {'GOOGLE_CLIENT_ID': 'test-google-client'})
    @patch('core.views.google_auth.requests.get')
    def test_registration_populates_photo_without_google_password(self, get):
        get.return_value = Mock(status_code=200, json=lambda: self.payload)
        response = self.client.post('/api/auth/google/', {'credential': 'fake-id-token'})
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(email='photo-google@test.com')
        self.assertEqual(user.name, 'Google Test User')
        self.assertEqual(user.google_photo_url, self.payload['picture'])
        self.assertFalse(user.has_usable_password())

    @patch.dict(os.environ, {'GOOGLE_CLIENT_ID': 'test-google-client'})
    @patch('core.views.google_auth.requests.get')
    def test_invalid_photo_host_is_discarded(self, get):
        payload = {**self.payload, 'picture': 'https://example.org/untrusted.png'}
        get.return_value = Mock(status_code=200, json=lambda: payload)
        response = self.client.post('/api/auth/google/', {'credential': 'fake-id-token'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.get(email=payload['email']).google_photo_url, '')

    @patch.dict(os.environ, {'GOOGLE_CLIENT_ID': 'test-google-client'})
    @patch('core.views.google_auth.requests.get')
    def test_second_login_updates_photo_and_preserves_name(self, get):
        get.return_value = Mock(status_code=200, json=lambda: self.payload)
        self.client.post('/api/auth/google/', {'credential': 'fake-id-token'})
        payload = {**self.payload, 'picture': 'https://lh3.googleusercontent.com/a/new-photo', 'name': 'Changed Name'}
        get.return_value = Mock(status_code=200, json=lambda: payload)
        response = self.client.post('/api/auth/google/', {'credential': 'fake-id-token'})
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(email=payload['email'])
        self.assertEqual(user.google_photo_url, payload['picture'])
        self.assertEqual(user.name, 'Google Test User')
