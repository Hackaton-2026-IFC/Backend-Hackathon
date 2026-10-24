from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Projeto, ProjetoMembro, Tarefa

User = get_user_model()


class MeuDiaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='myday@example.com', password='SenhaTeste123')
        self.other = User.objects.create_user(email='otherday@example.com', password='SenhaTeste123')
        self.project = Projeto.objects.create(nome='Meu Dia', criador=self.user)
        ProjetoMembro.objects.create(projeto=self.project, usuario=self.user, cargo='owner')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_only_accessible_tasks_and_limit(self):
        for n in range(3):
            Tarefa.objects.create(projeto=self.project, titulo=f'Minha tarefa {n}', data_limite=timezone.localdate() + timedelta(days=n))
        foreign = Projeto.objects.create(nome='Privado', criador=self.other)
        ProjetoMembro.objects.create(projeto=foreign, usuario=self.other, cargo='owner')
        Tarefa.objects.create(projeto=foreign, titulo='Nao deve aparecer')
        response = self.client.get('/api/meu-dia/?limite=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_pendentes'], 3)
        self.assertEqual(len(response.data['recomendacoes']), 2)
        self.assertTrue(all(x['tarefa']['projeto'] == self.project.pk for x in response.data['recomendacoes']))
