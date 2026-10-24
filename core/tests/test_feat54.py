from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from core.models.atividade import Atividade
from core.models.comentario_tarefa import ComentarioTarefa

User = get_user_model()

class ComentariosTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='comment-owner@test.com', password='12345678')
        self.other = User.objects.create_user(email='comment-other@test.com', password='12345678')
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        project = self.client.post('/api/projetos/', {'nome':'Project'}, format='json').data['id']
        self.task = self.client.post('/api/tarefas/', {'projeto':project, 'titulo':'Tarefa'}, format='json').data['id']
        self.url=f'/api/tarefas/{self.task}/comentarios/'

    def test_crud_and_feed(self):
        response=self.client.post(self.url, {'conteudo':'Vamos começar'}, format='json')
        self.assertEqual(response.status_code,201)
        pk=response.data['id']
        self.assertEqual(self.client.get(self.url).data['results'][0]['conteudo'],'Vamos começar')
        self.assertEqual(self.client.patch(f'{self.url}{pk}/', {'conteudo':'Já comecei'},format='json').status_code,200)
        self.assertTrue(Atividade.objects.filter(tarefa_id_original=self.task,acao='comentario_editado').exists())
        self.assertEqual(self.client.delete(f'{self.url}{pk}/').status_code,204)
        self.assertTrue(Atividade.objects.filter(tarefa_id_original=self.task,acao='comentario_excluido').exists())
        self.assertEqual(ComentarioTarefa.objects.count(),0)

    def test_permissions_and_validation(self):
        created=self.client.post(self.url,{'conteudo':'Olá'},format='json')
        self.assertEqual(self.client.post(self.url,{'conteudo':'   '},format='json').status_code,400)
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.get(self.url).status_code,403)
        self.assertEqual(self.client.patch(f'{self.url}{created.data["id"]}/',{'conteudo':'hack'},format='json').status_code,403)
