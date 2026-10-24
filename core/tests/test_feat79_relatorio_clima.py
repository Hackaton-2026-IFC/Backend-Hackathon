from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from core.models import Projeto, ProjetoMembro, Tarefa
from core.services.ai_agent import build_project_context, local_report

User = get_user_model()


class RelatorioClimaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='clima79@example.com', password='SenhaTeste123!')
        self.project = Projeto.objects.create(nome='Projeto climático', criador=self.user)
        ProjetoMembro.objects.get_or_create(projeto=self.project, usuario=self.user, defaults={'cargo': 'owner'})
        self.tomorrow = timezone.localdate() + timedelta(days=1)
        self.task = Tarefa.objects.create(
            projeto=self.project, titulo='Atividade externa', clima_influencia=True,
            localizacao='Joinville', data_limite=self.tomorrow,
        )

    @patch('core.services.ai_agent.forecast_for_task')
    def test_previsao_e_passada_ao_contexto(self, forecast):
        forecast.return_value = {
            'disponivel': True, 'data': self.tomorrow.isoformat(),
            'probabilidade_chuva_pct': 85, 'fonte': 'Open-Meteo',
        }
        context = build_project_context(self.project, self.user)
        task = context['tarefas'][0]
        self.assertTrue(task['clima_influencia'])
        self.assertEqual(task['localizacao'], 'Joinville')
        self.assertEqual(task['previsao']['probabilidade_chuva_pct'], 85)
        self.assertEqual(context['total_tarefas_com_clima'], 1)
        forecast.assert_called_once()

    @patch('core.services.ai_agent.forecast_for_task')
    def test_relatorio_local_alerta_chuva(self, forecast):
        forecast.return_value = {
            'disponivel': True, 'data': self.tomorrow.isoformat(),
            'probabilidade_chuva_pct': 85,
        }
        context = build_project_context(self.project, self.user)
        report = local_report(context, [], '')
        self.assertIn('Alerta de chuva', report)
        self.assertIn('85%', report)
        self.assertIn('Atividade externa', report)

    @patch('core.services.ai_agent.forecast_for_task')
    def test_previsao_indisponivel_nao_significa_sem_chuva(self, forecast):
        forecast.return_value = {'disponivel': False, 'motivo': 'Serviço meteorológico indisponível.'}
        context = build_project_context(self.project, self.user)
        report = local_report(context, [], '')
        self.assertIn('previsão não verificada', report)
        self.assertNotIn('Alerta de chuva', report)

    @patch('core.services.ai_agent.forecast_for_task')
    def test_prazo_distante_nao_consulta_api(self, forecast):
        self.task.data_limite = timezone.localdate() + timedelta(days=60)
        self.task.save()
        context = build_project_context(self.project, self.user)
        forecast.assert_not_called()
        self.assertFalse(context['tarefas'][0]['previsao']['disponivel'])

    @patch('core.services.ai_agent.forecast_for_task')
    def test_tarefa_sem_influencia_nao_consulta_api(self, forecast):
        self.task.clima_influencia = False
        self.task.save()
        context = build_project_context(self.project, self.user)
        forecast.assert_not_called()
        self.assertFalse(context['tarefas'][0]['clima_influencia'])

    @patch('core.services.ai_agent.forecast_for_task')
    def test_limita_consultas_em_cinco_tarefas(self, forecast):
        forecast.return_value = {'disponivel': True, 'probabilidade_chuva_pct': 20}
        for index in range(7):
            Tarefa.objects.create(
                projeto=self.project, titulo=f'Atividade {index}',
                clima_influencia=True, localizacao='Joinville', data_limite=self.tomorrow,
            )
        context = build_project_context(self.project, self.user)
        self.assertEqual(forecast.call_count, 5)
        unverified = [t for t in context['tarefas'] if t.get('previsao', {}).get('motivo', '').startswith('Limite de previsões')]
        self.assertEqual(len(unverified), 3)
