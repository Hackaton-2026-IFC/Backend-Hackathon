from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

User = get_user_model()


class DashboardIndicadoresTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='dashboard@example.com', password='SenhaForte123')
        self.outro = User.objects.create_user(email='fora-dashboard@example.com', password='SenhaForte123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        projeto = self.client.post('/api/projetos/', {'nome': 'Dashboard'}, format='json')
        self.assertEqual(projeto.status_code, 201, projeto.data)
        self.projeto = projeto.data['id']

    def criar_tarefa(self, titulo, status='planejado', dias=None, antecipado=None, urgencia_manual=None):
        dados = {'projeto': self.projeto, 'titulo': titulo, 'status': status}
        hoje = timezone.localdate()
        if dias is not None:
            dados['data_limite'] = (hoje + timedelta(days=dias)).isoformat()
        if antecipado is not None:
            dados['prazo_antecipado'] = (hoje + timedelta(days=antecipado)).isoformat()
        if urgencia_manual is not None:
            dados['urgencia_manual'] = urgencia_manual
        resposta = self.client.post('/api/tarefas/', dados, format='json')
        self.assertEqual(resposta.status_code, 201, resposta.data)
        return resposta.data

    def test_dashboard_do_projeto_retorna_progresso_urgencia_e_atrasos(self):
        self.criar_tarefa('Atrasada', dias=-2)
        self.criar_tarefa('Urgente', dias=20, antecipado=1)
        self.criar_tarefa('Andamento', status='em_andamento', dias=10)
        self.criar_tarefa('Concluida', status='concluido', dias=-5)

        resposta = self.client.get(f'/api/projetos/{self.projeto}/dashboard/')
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual(resposta.data['progresso'], 25.0)
        self.assertEqual(resposta.data['tarefas']['total'], 4)
        self.assertEqual(resposta.data['tarefas']['concluidas'], 1)
        self.assertEqual(resposta.data['tarefas']['atrasadas'], 1)
        self.assertEqual(resposta.data['urgencias']['muito_alta'], 1)
        self.assertEqual(resposta.data['urgencias']['alta'], 1)
        self.assertEqual(resposta.data['urgencias']['baixa'], 1)
        self.assertEqual(len(resposta.data['tarefas_atrasadas']), 1)
        self.assertEqual(resposta.data['tarefas_atrasadas'][0]['titulo'], 'Atrasada')

    def test_dashboard_geral_agrega_apenas_projetos_do_usuario(self):
        self.criar_tarefa('Minha tarefa', dias=1)
        projeto_outro = self.client.post('/api/projetos/', {'nome': 'Outro meu'}, format='json')
        self.assertEqual(projeto_outro.status_code, 201)
        self.client.post(
            '/api/tarefas/',
            {'projeto': projeto_outro.data['id'], 'titulo': 'Outra', 'status': 'concluido'},
            format='json',
        )

        resposta = self.client.get('/api/projetos/dashboard/')
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual(resposta.data['total_projetos'], 2)
        self.assertEqual(resposta.data['total_tarefas'], 2)
        self.assertEqual(resposta.data['tarefas_concluidas'], 1)
        self.assertEqual(resposta.data['progresso_geral'], 50.0)

    def test_nao_membro_nao_acessa_dashboard_do_projeto(self):
        self.client.force_authenticate(user=self.outro)
        resposta = self.client.get(f'/api/projetos/{self.projeto}/dashboard/')
        self.assertEqual(resposta.status_code, 403)

    def test_dashboard_vazio_retorna_zero(self):
        resposta = self.client.get(f'/api/projetos/{self.projeto}/dashboard/')
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data['progresso'], 0)
        self.assertEqual(resposta.data['tarefas']['total'], 0)
        self.assertEqual(resposta.data['tarefas']['atrasadas'], 0)
