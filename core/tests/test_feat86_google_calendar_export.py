from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Projeto, ProjetoMembro
from core.models.calendar_event import CalendarEvent
from core.models.google_calendar_export import GoogleCalendarExport
from core.models.google_identity import GoogleIdentity

User = get_user_model()


class GoogleCalendarExportTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='exportador@example.com', password='senha123')
        self.member = User.objects.create_user(email='membro@example.com', password='senha123')
        self.project = Projeto.objects.create(nome='Projeto de teste', criador=self.owner)
        ProjetoMembro.objects.create(projeto=self.project, usuario=self.owner, cargo='owner')
        ProjetoMembro.objects.create(projeto=self.project, usuario=self.member, cargo='member')
        self.event = CalendarEvent.objects.create(
            projeto=self.project, titulo='Apresentação', data=timezone.localdate()
        )
        GoogleIdentity.objects.create(user=self.owner, sub='google-owner')
        self.client = APIClient()
        token = RefreshToken.for_user(self.owner)
        token['auth_provider'] = 'google'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        self.calendar_url = f'/api/projetos/{self.project.pk}/calendario/'
        self.export_url = f'/api/projetos/{self.project.pk}/google-agenda/'

    def google_mocks(self, get, post):
        info = Mock(status_code=200)
        info.raise_for_status.return_value = None
        info.json.return_value = {'scope': 'openid https://www.googleapis.com/auth/calendar.events'}
        userinfo = Mock(status_code=200)
        userinfo.raise_for_status.return_value = None
        userinfo.json.return_value = {'sub': 'google-owner'}
        get.side_effect = [info, userinfo]
        result = Mock(status_code=201)
        result.json.return_value = {'id': 'google-id-1', 'htmlLink': 'https://calendar.google.com/event?eid=123'}
        post.return_value = result

    @patch('core.views.calendario.requests.post')
    @patch('core.views.calendario.requests.get')
    def test_status_persists_after_refresh_and_prevents_duplicate(self, get, post):
        self.google_mocks(get, post)
        before = self.client.get(self.calendar_url)
        self.assertFalse(before.data['eventos'][0]['exportado_google'])
        first = self.client.post(self.export_url, {'evento': self.event.pk, 'access_token': 'google-access'}, format='json')
        self.assertEqual(first.status_code, 201)
        self.assertFalse(first.data['ja_exportado'])
        self.assertEqual(GoogleCalendarExport.objects.count(), 1)
        after = self.client.get(self.calendar_url)
        self.assertTrue(after.data['eventos'][0]['exportado_google'])
        self.assertEqual(after.data['eventos'][0]['google_event_url'], 'https://calendar.google.com/event?eid=123')
        repeat = self.client.post(self.export_url, {'evento': self.event.pk, 'access_token': 'google-access'}, format='json')
        self.assertEqual(repeat.status_code, 200)
        self.assertTrue(repeat.data['ja_exportado'])
        post.assert_called_once()

    def test_export_status_is_private_to_each_user(self):
        GoogleCalendarExport.objects.create(evento=self.event, usuario=self.owner, google_event_id='g-1')
        token = RefreshToken.for_user(self.member)
        token['auth_provider'] = 'google'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        listing = self.client.get(self.calendar_url)
        self.assertEqual(listing.status_code, 200)
        self.assertFalse(listing.data['eventos'][0]['exportado_google'])
        self.assertIsNone(listing.data['eventos'][0]['google_event_url'])

    def test_deleting_event_removes_export_record(self):
        GoogleCalendarExport.objects.create(evento=self.event, usuario=self.owner, google_event_id='g-1')
        response = self.client.delete(f'{self.calendar_url}{self.event.pk}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(GoogleCalendarExport.objects.exists())
