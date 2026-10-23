from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from core.models.atividade import Atividade

User=get_user_model()
class FeedTests(TestCase):
    def setUp(self):
        self.owner=User.objects.create_user(email='feed-owner@test.com',password='12345678')
        self.out=User.objects.create_user(email='feed-out@test.com',password='12345678')
        self.client=APIClient()
        self.client.force_authenticate(user=self.owner)
        self.project=self.client.post('/api/projetos/',{'nome':'Feed'},format='json').data['id']

    def test_create_update_delete_and_permissions(self):
        result=self.client.post('/api/tarefas/',{'projeto':self.project,'titulo':'Implementar feed'},format='json')
        self.assertEqual(result.status_code,201)
        pk=result.data['id']
        self.assertEqual(Atividade.objects.filter(tarefa_id_original=pk).count(),1)
        change=self.client.patch(f'/api/tarefas/{pk}/',{'status':'em_andamento'},format='json')
        self.assertEqual(change.status_code,200)
        self.assertEqual(Atividade.objects.filter(tarefa_id_original=pk).count(),2)
        history=self.client.get(f'/api/tarefas/{pk}/atividades/')
        self.assertEqual(history.status_code,200)
        self.assertEqual(history.data['results'][0]['alteracoes']['status']['depois'],'em_andamento')
        self.client.force_authenticate(user=self.out)
        self.assertEqual(self.client.get(f'/api/projetos/{self.project}/atividades/').status_code,403)
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.delete(f'/api/tarefas/{pk}/').status_code,204)
        self.assertTrue(Atividade.objects.filter(tarefa_id_original=pk,acao='tarefa_excluida').exists())
        self.assertEqual(self.client.get(f'/api/projetos/{self.project}/atividades/').data['results'][0]['tarefa'],None)
