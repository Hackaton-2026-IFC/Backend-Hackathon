from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Recurso, ProjetoMembro

User = get_user_model()


class RecursosTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='rec-owner@example.com', password='SenhaForte123')
        self.member = User.objects.create_user(email='rec-member@example.com', password='SenhaForte123')
        self.outsider = User.objects.create_user(email='rec-outsider@example.com', password='SenhaForte123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        self.projeto = self.client.post('/api/projetos/', {'nome': 'Projeto Recursos'}, format='json').data['id']
        self.outro = self.client.post('/api/projetos/', {'nome': 'Outro Projeto'}, format='json').data['id']
        self.tarefa = self.client.post('/api/tarefas/', {'projeto': self.projeto, 'titulo': 'Tarefa A'}, format='json').data['id']
        self.tarefa_outro = self.client.post('/api/tarefas/', {'projeto': self.outro, 'titulo': 'Tarefa B'}, format='json').data['id']
        ProjetoMembro.objects.create(projeto_id=self.projeto, usuario=self.member, cargo='member')
        self.dados = {'titulo': 'Especificação', 'url': 'https://example.com/doc', 'tipo': 'documento'}

    def test_criar_listar_editar_e_excluir_recurso_do_projeto(self):
        url = f'/api/projetos/{self.projeto}/recursos/'
        resp = self.client.post(url, self.dados, format='json')
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['projeto'], self.projeto)
        self.assertIsNone(resp.data['tarefa'])
        self.assertEqual(len(self.client.get(url).data), 1)
        rid = resp.data['id']
        self.assertEqual(self.client.patch(f'/api/recursos/{rid}/', {'titulo': 'Atualizado'}, format='json').status_code, 200)
        self.assertEqual(self.client.delete(f'/api/recursos/{rid}/').status_code, 204)
        self.assertFalse(Recurso.objects.filter(pk=rid).exists())

    def test_tarefa_pertence_ao_projeto_correto(self):
        resp = self.client.post(f'/api/tarefas/{self.tarefa}/recursos/', self.dados, format='json')
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['projeto'], self.projeto)
        self.assertEqual(resp.data['tarefa'], self.tarefa)
        self.assertEqual(len(self.client.get(f'/api/tarefas/{self.tarefa}/recursos/').data), 1)
        self.assertEqual(len(self.client.get(f'/api/projetos/{self.projeto}/recursos/').data), 1)
        self.assertEqual(len(self.client.get(f'/api/projetos/{self.outro}/recursos/').data), 0)

    def test_membro_pode_criar_mas_nao_apagar_recurso_de_outro(self):
        rid = self.client.post(f'/api/projetos/{self.projeto}/recursos/', self.dados, format='json').data['id']
        self.client.force_authenticate(user=self.member)
        self.assertEqual(self.client.get(f'/api/projetos/{self.projeto}/recursos/').status_code, 200)
        self.assertEqual(self.client.patch(f'/api/recursos/{rid}/', {'titulo': 'Hack'}, format='json').status_code, 403)
        self.assertEqual(self.client.delete(f'/api/recursos/{rid}/').status_code, 403)
        self.assertEqual(self.client.post(f'/api/projetos/{self.projeto}/recursos/', self.dados, format='json').status_code, 201)

    def test_nao_membro_nao_acessa_recursos(self):
        rid = self.client.post(f'/api/projetos/{self.projeto}/recursos/', self.dados, format='json').data['id']
        self.client.force_authenticate(user=self.outsider)
        self.assertEqual(self.client.get(f'/api/projetos/{self.projeto}/recursos/').status_code, 403)
        self.assertEqual(self.client.get(f'/api/tarefas/{self.tarefa}/recursos/').status_code, 403)
        self.assertEqual(self.client.get(f'/api/recursos/{rid}/').status_code, 404)
        self.assertIn(self.client.post(f'/api/projetos/{self.projeto}/recursos/', self.dados, format='json').status_code, (403, 404))

    def test_url_invalida_e_campos_de_vinculo_nao_podem_ser_forcados(self):
        url = f'/api/projetos/{self.projeto}/recursos/'
        self.assertEqual(self.client.post(url, {**self.dados, 'url': 'javascript:alert(1)'}, format='json').status_code, 400)
        resp = self.client.post(url, {**self.dados, 'tarefa': self.tarefa_outro, 'projeto': self.outro}, format='json')
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertIsNone(resp.data['tarefa'])
        self.assertEqual(resp.data['projeto'], self.projeto)
        patch = self.client.patch(f"/api/recursos/{resp.data['id']}/", {'tarefa': self.tarefa_outro, 'projeto': self.outro}, format='json')
        self.assertEqual(patch.status_code, 200)
        self.assertEqual(patch.data['projeto'], self.projeto)
        self.assertIsNone(patch.data['tarefa'])
