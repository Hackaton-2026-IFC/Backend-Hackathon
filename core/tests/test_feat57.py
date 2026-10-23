from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from core.models import ProjetoMembro

User = get_user_model()


class NotificationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='notify-owner@test.com', password='12345678', name='Owner')
        self.member = User.objects.create_user(email='notify-member@test.com', password='12345678', name='Member')
        self.outsider = User.objects.create_user(email='notify-out@test.com', password='12345678')
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        self.project = self.client.post('/api/projetos/', {'nome': 'Notify'}, format='json').data['id']
        ProjetoMembro.objects.create(projeto_id=self.project, usuario=self.member, cargo=ProjetoMembro.CARGO_MEMBER)

    def test_site_notification_is_private_and_readable(self):
        task = self.client.post(
            '/api/tarefas/',
            {'projeto': self.project, 'titulo': 'Nova tarefa'},
            format='json',
        )
        self.assertEqual(task.status_code, 201)

        self.client.force_authenticate(user=self.member)
        notifications = self.client.get('/api/notificacoes/')
        self.assertEqual(notifications.status_code, 200)
        self.assertEqual(len(notifications.data['results']), 1)
        notification_id = notifications.data['results'][0]['id']
        self.assertFalse(notifications.data['results'][0]['lida'])
        self.assertEqual(self.client.get('/api/notificacoes/nao-lidas/').data['quantidade'], 1)
        self.assertEqual(self.client.post(f'/api/notificacoes/{notification_id}/ler/').status_code, 200)
        self.assertEqual(self.client.get('/api/notificacoes/nao-lidas/').data['quantidade'], 0)

        self.client.force_authenticate(user=self.outsider)
        self.assertEqual(len(self.client.get('/api/notificacoes/').data['results']), 0)

    @override_settings(
        NOTIFICATION_EMAIL_ENABLED=True,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='hackathon@test.com',
    )
    def test_email_can_be_sent(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                '/api/tarefas/',
                {'projeto': self.project, 'titulo': 'Avisar por e-mail'},
                format='json',
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['notify-member@test.com'])
        self.assertIn('Nova tarefa', mail.outbox[0].subject)

    def test_comment_notifies_other_members(self):
        task_id = self.client.post(
            '/api/tarefas/',
            {'projeto': self.project, 'titulo': 'Conversar'},
            format='json',
        ).data['id']
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            f'/api/tarefas/{task_id}/comentarios/',
            {'conteudo': 'Atualizei aqui'},
            format='json',
        )
        self.assertEqual(response.status_code, 201)

        self.client.force_authenticate(user=self.owner)
        titles = [item['titulo'] for item in self.client.get('/api/notificacoes/').data['results']]
        self.assertIn('Novo comentário', titles)
