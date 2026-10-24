import os
from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase

from core.services.ai_agent import _extract_output_text, generate_project_analysis


class AgentServiceTests(SimpleTestCase):
    def setUp(self):
        self.context = {
            'projeto': {'nome': 'Projeto teste'},
            'tarefas': [],
            'total_tarefas_projeto': 0,
        }

    def test_extract_response_text(self):
        payload = {'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': 'Relatório OK'}]}]}
        self.assertEqual(_extract_output_text(payload), 'Relatório OK')

    @patch('core.services.ai_agent.build_project_context')
    @patch('core.services.ai_agent.requests.post')
    @patch.dict(os.environ, {'OPENAI_API_KEY': '', 'OPENAI_MODEL': 'gpt-4.1-mini'})
    def test_missing_key_uses_local_report(self, post, context):
        context.return_value = self.context
        result = generate_project_analysis(None, None, [], '')
        self.assertEqual(result['modo'], 'local')
        post.assert_not_called()

    @patch('core.services.ai_agent.build_project_context')
    @patch('core.services.ai_agent.requests.post')
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-only', 'OPENAI_MODEL': ''})
    def test_empty_model_uses_valid_default(self, post, context):
        context.return_value = self.context
        post.return_value = Mock(json=lambda: {'output_text': 'Relatório OK'})
        post.return_value.raise_for_status.return_value = None
        result = generate_project_analysis(None, None, ['ideia'], 'objetivo')
        self.assertEqual(result['modo'], 'openai')
        self.assertEqual(post.call_args.kwargs['json']['model'], 'gpt-4.1-mini')

    @patch('core.services.ai_agent.build_project_context')
    @patch('core.services.ai_agent.requests.post')
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-only'})
    def test_timeout_uses_local_report(self, post, context):
        context.return_value = self.context
        post.side_effect = requests.Timeout('timeout')
        result = generate_project_analysis(None, None, [], '')
        self.assertEqual(result['modo'], 'local')

    @patch('core.services.ai_agent.build_project_context')
    @patch('core.services.ai_agent.requests.post')
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-only'})
    def test_http_error_uses_local_report(self, post, context):
        context.return_value = self.context
        response = Mock(status_code=429)
        post.return_value.raise_for_status.side_effect = requests.HTTPError('rate limited', response=response)
        result = generate_project_analysis(None, None, [], '')
        self.assertEqual(result['modo'], 'local')
