from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Projeto, ProjetoMembro, Tarefa

User = get_user_model()


class AccessIsolationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner-isolation@example.com', password='SenhaTeste123')
        self.stranger = User.objects.create_user(email='stranger-isolation@example.com', password='SenhaTeste123')
        self.project = Projeto.objects.create(nome='Projeto privado', criador=self.owner)
        ProjetoMembro.objects.create(projeto=self.project, usuario=self.owner, cargo='owner')
        self.task = Tarefa.objects.create(projeto=self.project, titulo='Tarefa privada')
        self.client = APIClient()
        self.client.force_authenticate(user=self.stranger)

    def test_outsider_cannot_read_project_feed(self):
        response = self.client.get(f'/api/projetos/{self.project.pk}/atividades/')
        self.assertEqual(response.status_code, 403)

    def test_outsider_cannot_read_task_feed(self):
        response = self.client.get(f'/api/tarefas/{self.task.pk}/atividades/')
        self.assertEqual(response.status_code, 403)

    def test_outsider_cannot_read_project_calendar(self):
        response = self.client.get(f'/api/projetos/{self.project.pk}/calendario/')
        self.assertEqual(response.status_code, 403)

    def test_outsider_cannot_read_task_comments(self):
        response = self.client.get(f'/api/tarefas/{self.task.pk}/comentarios/')
        self.assertIn(response.status_code, (403, 404))
