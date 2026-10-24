from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from core.models import Projeto, ProjetoMembro, Tarefa

User = get_user_model()

class MeuDiaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='owner@dev.com', password='senha123')
        self.other = User.objects.create_user(email='outro@dev.com', password='senha123')
        self.proj = Projeto.objects.create(nome='Projetinho', criador=self.user)
        ProjetoMembro.objects.create(projeto=self.proj, usuario=self.user, cargo='owner')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_priorities_and_privacy(self):
        high = Tarefa.objects.create(projeto=self.proj, titulo='Prioritária', prioridade='muito_alta', responsavel=self.user)
        low = Tarefa.objects.create(projeto=self.proj, titulo='Menos prioritária', prioridade='baixa')
        blocked = Tarefa.objects.create(projeto=self.proj, titulo='Bloqueada', prioridade='muito_alta')
        blocked.dependencias.add(high)
        resp = self.client.get('/api/meu-dia/')
        self.assertEqual(resp.status_code, 200)
        ids = [item['tarefa']['id'] for item in resp.data['recomendacoes']]
        self.assertIn(high.id, ids)
        self.assertIn(low.id, ids)
        self.assertTrue(next(x for x in resp.data['recomendacoes'] if x['tarefa']['id'] == blocked.id)['bloqueada'])
        self.assertEqual(ids[-1], blocked.id)

    def test_unauthenticated(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get('/api/meu-dia/').status_code, 401)
