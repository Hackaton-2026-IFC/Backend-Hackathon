import os
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


class ProjectAgentTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='agent-owner@test.com', password='12345678', name='Owner')
        self.outsider = User.objects.create_user(email='agent-out@test.com', password='12345678')
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        self.project = self.client.post('/api/projetos/', {'nome': 'Agente'}, format='json').data['id']
        self.client.post(
            '/api/tarefas/',
            {'projeto': self.project, 'titulo': 'Criar API', 'status': 'em_andamento'},
            format='json',
        )
        self.client.post(
            '/api/notas/',
            {'projeto': self.project, 'titulo': 'Ideia', 'conteudo': 'Gerar relatório'},
            format='json',
        )
        self.url = f'/api/projetos/{self.project}/agente/'

    @patch.dict(os.environ, {}, clear=False)
    def test_fallback_local_sem_chave(self):
        os.environ.pop('OPENAI_API_KEY', None)
        response = self.client.post(
            self.url,
            {'objetivo': 'Entregar MVP', 'ideias': ['Automatizar relatório']},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['modo'], 'local')
        self.assertIn('Relatório', response.data['analise'])
        self.assertIn('Automatizar relatório', response.data['analise'])

    @patch('core.services.ai_agent.requests.post')
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key', 'OPENAI_MODEL': 'gpt-6-luna'})
    def test_openai_quando_configurada(self, post):
        post.return_value = Mock(
            json=lambda: {'output_text': 'Relatório inteligente'},
            raise_for_status=lambda: None,
        )
        response = self.client.post(self.url, {'ideias': ['Feed inteligente']}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['modo'], 'openai')
        self.assertEqual(response.data['analise'], 'Relatório inteligente')
        headers = post.call_args.kwargs['headers']
        self.assertEqual(headers['Authorization'], 'Bearer test-key')

    def test_bloqueia_usuario_fora_do_projeto(self):
        self.client.force_authenticate(user=self.outsider)
        self.assertEqual(self.client.post(self.url, {}, format='json').status_code, 403)

    def test_limita_entrada(self):
        response = self.client.post(self.url, {'ideias': ['x'] * 21}, format='json')
        self.assertEqual(response.status_code, 400)
