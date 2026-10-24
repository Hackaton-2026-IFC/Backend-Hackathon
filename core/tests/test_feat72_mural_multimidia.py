from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from core.models import Nota

User = get_user_model()


class MuralMultimidiaTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.media.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.user = User.objects.create_user(email='mural-owner@test.com', password='TestPass123!')
        self.other = User.objects.create_user(email='mural-other@test.com', password='TestPass123!')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @staticmethod
    def image_file(filename='ideia.png'):
        buffer = BytesIO()
        Image.new('RGB', (3, 3), color=(35, 85, 120)).save(buffer, format='PNG')
        return SimpleUploadedFile(filename, buffer.getvalue(), content_type='image/png')

    def test_idea_with_image_only_uploads_and_can_update_text_and_link(self):
        response = self.client.post('/api/notas/', {'imagem': self.image_file()}, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        note_id = response.data['id']
        self.assertIn('/media/', response.data['imagem_url'])
        self.assertNotIn('imagem', response.data)
        response = self.client.patch(f'/api/notas/{note_id}/', {
            'titulo': 'Wireframe', 'conteudo': 'Testar layout', 'link': 'https://example.org/design',
        }, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['link'], 'https://example.org/design')
        self.assertTrue(response.data['imagem_url'])
        response = self.client.patch(f'/api/notas/{note_id}/', {'imagem': None}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIsNone(response.data['imagem_url'])

    def test_link_only_and_normal_old_notes_still_work(self):
        link = self.client.post('/api/notas/', {'link': 'https://example.com/referencia'}, format='json')
        self.assertEqual(link.status_code, 201, link.data)
        self.assertEqual(link.data['link'], 'https://example.com/referencia')
        old = self.client.post('/api/notas/', {'titulo': 'Nota comum'}, format='json')
        self.assertEqual(old.status_code, 201, old.data)
        self.assertEqual(old.data['link'], '')
        self.assertIsNone(old.data['imagem_url'])

    def test_validation_blocks_unsafe_link_and_non_image_upload(self):
        bad_link = self.client.post('/api/notas/', {'link': 'ftp://example.com/file'}, format='json')
        self.assertEqual(bad_link.status_code, 400)
        self.assertEqual(Nota.objects.count(), 0)
        bad_file = SimpleUploadedFile('fake.png', b'<script>evil</script>', content_type='image/png')
        response = self.client.post('/api/notas/', {'imagem': bad_file}, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Nota.objects.count(), 0)
        empty = self.client.post('/api/notas/', {}, format='json')
        self.assertEqual(empty.status_code, 400)

    def test_image_notes_are_private_through_the_api(self):
        created = self.client.post('/api/notas/', {'imagem': self.image_file(), 'titulo': 'Particular'}, format='multipart')
        self.assertEqual(created.status_code, 201, created.data)
        note_id = created.data['id']
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.get(f'/api/notas/{note_id}/').status_code, 404)
        self.assertEqual(self.client.patch(f'/api/notas/{note_id}/', {'link': 'https://example.com'}, format='json').status_code, 404)
        self.assertEqual(self.client.delete(f'/api/notas/{note_id}/').status_code, 404)
        self.assertEqual(self.client.get('/api/notas/').data['results'], [])
