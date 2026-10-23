from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Projeto

User = get_user_model()


class ProjectPlanningFieldsTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='feat4owner@example.com', password='StrongPassword123')
        self.other = User.objects.create_user(email='feat4other@example.com', password='StrongPassword123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

    def test_project_has_default_status_and_optional_deadline(self):
        response = self.client.post('/api/projetos/', {'nome': 'Projeto inicial'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['status'], 'planejado')
        self.assertIsNone(response.data['data_limite'])
        self.assertEqual(Projeto.objects.get(pk=response.data['id']).status, 'planejado')

    def test_can_create_and_change_project_planning(self):
        response = self.client.post(
            '/api/projetos/',
            {'nome': 'Aplicação', 'status': 'em_andamento', 'data_limite': '2026-12-10'},
            format='json',
        )
        self.assertEqual(response.status_code, 201, response.data)
        pid = response.data['id']
        self.assertEqual(Projeto.objects.get(pk=pid).data_limite, date(2026, 12, 10))
        update = self.client.patch(
            f'/api/projetos/{pid}/', {'status': 'concluido', 'data_limite': '2026-12-20'}, format='json'
        )
        self.assertEqual(update.status_code, 200, update.data)
        self.assertEqual(update.data['status'], 'concluido')
        self.assertEqual(update.data['data_limite'], '2026-12-20')

    def test_invalid_status_is_rejected_and_unrelated_user_cannot_update(self):
        response = self.client.post('/api/projetos/', {'nome': 'Bloqueado'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        pid = response.data['id']
        invalid = self.client.patch(f'/api/projetos/{pid}/', {'status': 'inexistente'}, format='json')
        self.assertEqual(invalid.status_code, 400)
        self.client.force_authenticate(user=self.other)
        denied = self.client.patch(f'/api/projetos/{pid}/', {'status': 'concluido'}, format='json')
        self.assertEqual(denied.status_code, 403)
