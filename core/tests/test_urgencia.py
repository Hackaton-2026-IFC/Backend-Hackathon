from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

User = get_user_model()

class UrgenciaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='urgencia@example.com', password='SenhaForte123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.projeto = self.client.post('/api/projetos/', {'nome': 'Projeto urgencia'}, format='json').data['id']

    def criar(self, dias, antecipado=None):
        hoje = timezone.localdate()
        dados = {'projeto': self.projeto, 'titulo': 'Teste', 'data_limite': (hoje + timedelta(days=dias)).isoformat()}
        if antecipado is not None:
            dados['prazo_antecipado'] = (hoje + timedelta(days=antecipado)).isoformat()
        res = self.client.post('/api/tarefas/', dados, format='json')
        self.assertEqual(res.status_code, 201, res.data)
        return res

    def test_cinco_niveis_automaticos(self):
        for dias, urgencia in [(-1, 'muito_alta'), (1, 'alta'), (5, 'neutra'), (10, 'baixa'), (25, 'muito_baixa')]:
            with self.subTest(dias=dias):
                self.assertEqual(self.criar(dias).data['urgencia'], urgencia)

    def test_antecipado_prevalece_sobre_oficial(self):
        self.assertEqual(self.criar(30, 1).data['urgencia'], 'alta')

    def test_urgencia_manual_pode_ser_removida(self):
        tarefa = self.criar(25)
        path = f"/api/tarefas/{tarefa.data['id']}/"
        update = self.client.patch(path, {'urgencia_manual': 'muito_alta'}, format='json')
        self.assertEqual(update.status_code, 200, update.data)
        self.assertEqual(update.data['urgencia'], 'muito_alta')
        self.assertEqual(self.client.patch(path, {'urgencia_manual': 'invalida'}, format='json').status_code, 400)
        update = self.client.patch(path, {'urgencia_manual': None}, format='json')
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.data['urgencia'], 'muito_baixa')

    def test_concluida_nao_tem_urgencia(self):
        tarefa = self.criar(0)
        res = self.client.patch(f"/api/tarefas/{tarefa.data['id']}/", {'status': 'concluido'}, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.assertIsNone(res.data['urgencia'])
