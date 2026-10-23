from datetime import timedelta
from unittest.mock import Mock, patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import Projeto, ProjetoMembro, Tarefa

User = get_user_model()

class ClimaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='owner@dev.com', password='senha123')
        self.other = User.objects.create_user(email='outro@dev.com', password='senha123')
        self.proj = Projeto.objects.create(nome='Projeto', criador=self.user)
        ProjetoMembro.objects.create(projeto=self.proj, usuario=self.user, cargo='owner')
        self.tarefa = Tarefa.objects.create(projeto=self.proj, titulo='Foto', clima_influencia=True,
            localizacao='Joinville', data_limite=timezone.localdate()+timedelta(days=2))
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_no_access_other_project(self):
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.get(f'/api/tarefas/{self.tarefa.id}/clima/').status_code, 403)

    @patch('core.services.weather.requests.get')
    def test_forecast(self, get):
        geo = Mock(status_code=200)
        geo.json.return_value = {'results': [{'name':'Joinville','latitude':-26.3,'longitude':-48.8}]}
        geo.raise_for_status.return_value = None
        meteo = Mock(status_code=200)
        meteo.json.return_value = {'daily': {
            'temperature_2m_max':[25], 'temperature_2m_min':[18],
            'precipitation_probability_max':[70], 'wind_speed_10m_max':[20]
        }}
        meteo.raise_for_status.return_value = None
        get.side_effect = [geo, meteo]
        resp = self.client.get(f'/api/tarefas/{self.tarefa.id}/clima/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['disponivel'])
        self.assertEqual(resp.data['probabilidade_chuva_pct'], 70)
