from datetime import timedelta
from unittest.mock import Mock, patch
from rest_framework_simplejwt.tokens import RefreshToken
from core.models.google_identity import GoogleIdentity
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import Projeto, ProjetoMembro, Tarefa
from core.models.calendar_event import CalendarEvent

User = get_user_model()

class CalendarTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@example.com', password='senha123')
        self.other = User.objects.create_user(email='other@example.com', password='senha123')
        self.project = Projeto.objects.create(nome='Projeto', criador=self.owner)
        ProjetoMembro.objects.create(projeto=self.project, usuario=self.owner, cargo='owner')
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        self.url = f'/api/projetos/{self.project.pk}/calendario/'

    def test_calendar_create_list_update_delete(self):
        today = timezone.localdate()
        payload = {'titulo': 'Reunião', 'data': today.isoformat(), 'hora_inicio': '10:00', 'hora_fim': '11:00'}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, 201)
        event_id = response.data['id']
        self.assertEqual(CalendarEvent.objects.count(), 1)
        Tarefa.objects.create(projeto=self.project, titulo='Entregar', data_limite=today)
        listing = self.client.get(self.url, {'inicio': today.isoformat(), 'fim': today.isoformat()})
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.data['eventos']), 1)
        self.assertEqual(len(listing.data['tarefas']), 1)
        patch_response = self.client.patch(f'{self.url}{event_id}/', {'titulo': 'Atualizada'}, format='json')
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.data['titulo'], 'Atualizada')
        self.assertEqual(self.client.delete(f'{self.url}{event_id}/').status_code, 204)

    def test_other_user_cannot_access_calendar(self):
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_google_calendar_requires_google_session(self):
        event = CalendarEvent.objects.create(projeto=self.project, titulo='Reunião', data=timezone.localdate())
        response = self.client.post(f'/api/projetos/{self.project.pk}/google-agenda/', {
            'evento': event.id, 'access_token': 'fake'
        }, format='json')
        self.assertEqual(response.status_code, 403)

    def test_validate_time_range(self):
        response = self.client.post(self.url, {
            'titulo': 'Erro', 'data': timezone.localdate().isoformat(),
            'hora_inicio': '14:00', 'hora_fim': '13:00',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    @patch('core.views.calendario.requests.post')
    @patch('core.views.calendario.requests.get')
    def test_google_export_requires_matching_account(self, get, post):
        GoogleIdentity.objects.create(user=self.owner, sub='google-sub')
        event = CalendarEvent.objects.create(projeto=self.project, titulo='Apresentação', data=timezone.localdate())
        token = RefreshToken.for_user(self.owner)
        token['auth_provider'] = 'google'
        self.client.force_authenticate(user=None)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        info = Mock(status_code=200)
        info.raise_for_status.return_value = None
        info.json.return_value = {'scope': 'openid https://www.googleapis.com/auth/calendar.events'}
        who = Mock(status_code=200)
        who.raise_for_status.return_value = None
        who.json.return_value = {'sub': 'google-sub'}
        get.side_effect = [info, who]
        sent = Mock(status_code=201)
        sent.json.return_value = {'id': 'event-g', 'htmlLink': 'https://calendar.google.com/event'}
        post.return_value = sent
        result = self.client.post(f'/api/projetos/{self.project.pk}/google-agenda/',
                                  {'evento': event.pk, 'access_token': 'valid'}, format='json')
        self.assertEqual(result.status_code, 201)
        self.assertEqual(result.data['id'], 'event-g')

    @patch('core.views.calendario.requests.get')
    def test_google_export_rejects_another_google_account(self, get):
        GoogleIdentity.objects.create(user=self.owner, sub='owner-sub')
        event = CalendarEvent.objects.create(projeto=self.project, titulo='Reunião', data=timezone.localdate())
        token = RefreshToken.for_user(self.owner)
        token['auth_provider'] = 'google'
        self.client.force_authenticate(user=None)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        info = Mock(status_code=200)
        info.raise_for_status.return_value = None
        info.json.return_value = {'scope': 'openid https://www.googleapis.com/auth/calendar.events'}
        who = Mock(status_code=200)
        who.raise_for_status.return_value = None
        who.json.return_value = {'sub': 'attacker-sub'}
        get.side_effect = [info, who]
        result = self.client.post(f'/api/projetos/{self.project.pk}/google-agenda/',
                                  {'evento': event.pk, 'access_token': 'valid'}, format='json')
        self.assertEqual(result.status_code, 403)
