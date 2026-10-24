import os
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Projeto, ProjetoMembro, Tarefa
from core.services.ai_agent import _extract_gemini_text

User = get_user_model()


class GeminiAgentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='gemini@example.com', password='StrongPass123')
        self.outsider = User.objects.create_user(email='outsider@example.com', password='StrongPass123')
        self.project = Projeto.objects.create(nome='Momentum Teste', criador=self.user)
        ProjetoMembro.objects.create(projeto=self.project, usuario=self.user, cargo='owner')
        Tarefa.objects.create(projeto=self.project, titulo='Criar API', criado_por=self.user)
        self.url = f'/api/projetos/{self.project.pk}/agente/'
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_extract_gemini_text(self):
        text = _extract_gemini_text({'candidates': [
            {'content': {'parts': [{'text': 'Relatório '}, {'text': 'pronto'}]}}
        ]})
        self.assertEqual(text, 'Relatório \npronto')

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'fake-gemini-key', 'GEMINI_MODEL': 'gemini-2.5-flash'})
    @patch('core.services.ai_agent.requests.post')
    def test_report_uses_gemini_and_keeps_frontend_contract(self, post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            'candidates': [{'content': {'parts': [{'text': '# Relatório com Gemini'}]}}]
        }
        post.return_value = response
        result = self.client.post(self.url, {
            'objetivo': 'Entregar MVP', 'ideias': ['Criar roadmap'],
        }, format='json')
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data['modo'], 'gemini')
        self.assertEqual(result.data['modelo'], 'gemini-2.5-flash')
        self.assertEqual(result.data['analise'], '# Relatório com Gemini')
        self.assertEqual(result.data['projeto'], self.project.pk)
        self.assertEqual(post.call_args.kwargs['headers']['x-goog-api-key'], 'fake-gemini-key')
        self.assertIn('gemini-2.5-flash:generateContent', post.call_args.args[0])
        self.assertIn('systemInstruction', post.call_args.kwargs['json'])

    @patch.dict(os.environ, {'GEMINI_API_KEY': ''})
    def test_missing_key_returns_local_report(self):
        result = self.client.post(self.url, {}, format='json')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['modo'], 'local')
        self.assertIn('GEMINI_API_KEY', result.data['aviso'])

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'fake-gemini-key'})
    @patch('core.services.ai_agent.requests.post')
    def test_gemini_failure_returns_local_report(self, post):
        post.side_effect = __import__('requests').Timeout()
        result = self.client.post(self.url, {}, format='json')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['modo'], 'local')
        self.assertIn('aviso', result.data)

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'fake-gemini-key'})
    @patch('core.services.ai_agent.requests.post')
    def test_non_member_cannot_send_project_to_gemini(self, post):
        self.client.force_authenticate(user=self.outsider)
        result = self.client.post(self.url, {}, format='json')
        self.assertEqual(result.status_code, 403)
        post.assert_not_called()
