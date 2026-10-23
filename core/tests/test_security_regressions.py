from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Projeto, ProjetoMembro, Tarefa

User = get_user_model()


class SecurityRegressionTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner-security@example.com', password='SenhaForte123')
        self.admin = User.objects.create_user(email='admin-security@example.com', password='SenhaForte123')
        self.guest = User.objects.create_user(email='guest-security@example.com', password='SenhaForte123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

    def create_project(self, name):
        response = self.client.post('/api/projetos/', {'nome': name}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        return response.data['id']

    def add_admin(self, project_id):
        response = self.client.post(
            f'/api/projetos/{project_id}/adicionar-membro/',
            {'usuario': self.admin.id, 'cargo': 'admin'},
            format='json',
        )
        self.assertEqual(response.status_code, 201, response.data)

    def test_user_cannot_edit_another_account_or_elevate_privileges(self):
        forbidden = self.client.patch(
            f'/api/usuarios/{self.admin.id}/', {'name': 'Conta sequestrada'}, format='json'
        )
        self.assertEqual(forbidden.status_code, 403)
        self.admin.refresh_from_db()
        self.assertNotEqual(self.admin.name, 'Conta sequestrada')

        response = self.client.patch(
            f'/api/usuarios/{self.owner.id}/',
            {'name': 'Novo Nome', 'is_staff': True, 'is_superuser': True, 'is_active': False},
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.name, 'Novo Nome')
        self.assertFalse(self.owner.is_staff)
        self.assertFalse(self.owner.is_superuser)
        self.assertTrue(self.owner.is_active)

        directory = self.client.get('/api/usuarios/')
        self.assertEqual(directory.status_code, 200)
        self.assertNotIn('is_superuser', directory.data['results'][0])
        self.assertNotIn('email', directory.data['results'][0])
        self.assertEqual(self.client.get(f'/api/usuarios/{self.admin.id}/').status_code, 403)
        self.assertEqual(self.client.post('/api/usuarios/', {'email': 'new@example.com'}).status_code, 405)
        self.assertEqual(self.client.delete(f'/api/usuarios/{self.admin.id}/').status_code, 405)

    def test_admin_cannot_grant_owner_role_or_demote_owner(self):
        project_id = self.create_project('Permissões')
        self.add_admin(project_id)
        self.client.force_authenticate(user=self.admin)

        elevation = self.client.post(
            f'/api/projetos/{project_id}/adicionar-membro/',
            {'usuario': self.admin.id, 'cargo': 'owner'},
            format='json',
        )
        self.assertEqual(elevation.status_code, 400)
        demotion = self.client.post(
            f'/api/projetos/{project_id}/adicionar-membro/',
            {'usuario': self.owner.id, 'cargo': 'admin'},
            format='json',
        )
        self.assertEqual(demotion.status_code, 400)

        self.assertTrue(
            ProjetoMembro.objects.filter(projeto_id=project_id, usuario=self.owner, cargo='owner').exists()
        )
        self.assertEqual(self.client.delete(f'/api/projetos/{project_id}/').status_code, 403)

    def test_full_project_update_does_not_transfer_creator(self):
        project_id = self.create_project('Original')
        self.add_admin(project_id)
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(
            f'/api/projetos/{project_id}/', {'nome': 'Renomeado', 'criador': self.admin.id}, format='json'
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(Projeto.objects.get(pk=project_id).criador_id, self.owner.id)

    def test_task_cannot_move_to_inaccessible_project_or_assign_foreign_user(self):
        own_project = self.create_project('Equipe A')
        other_project = self.create_project('Equipe B')
        self.add_admin(own_project)
        response = self.client.post('/api/tarefas/', {'projeto': own_project, 'titulo': 'Trabalho'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        task_id = response.data['id']

        self.client.force_authenticate(user=self.admin)
        move = self.client.patch(f'/api/tarefas/{task_id}/', {'projeto': other_project}, format='json')
        self.assertEqual(move.status_code, 400)
        assignment = self.client.patch(
            f'/api/tarefas/{task_id}/', {'responsavel': self.guest.id}, format='json'
        )
        self.assertEqual(assignment.status_code, 400)

        update = self.client.put(
            f'/api/tarefas/{task_id}/', {'projeto': own_project, 'titulo': 'Atualizado'}, format='json'
        )
        self.assertEqual(update.status_code, 200, update.data)
        task = Tarefa.objects.get(pk=task_id)
        self.assertEqual(task.projeto_id, own_project)
        self.assertEqual(task.criado_por_id, self.owner.id)

    def test_invitee_can_see_invitation_and_cannot_reply_twice(self):
        project_id = self.create_project('Convites')
        response = self.client.post(
            '/api/convites/', {'projeto': project_id, 'usuario': self.guest.id, 'cargo': 'admin'},
            format='json',
        )
        self.assertEqual(response.status_code, 201, response.data)
        invitation_id = response.data['id']

        self.client.force_authenticate(user=self.guest)
        listing = self.client.get('/api/convites/')
        self.assertEqual(listing.status_code, 200, listing.data)
        self.assertIn(invitation_id, [item['id'] for item in listing.data['results']])

        accepted = self.client.post(
            f'/api/convites/{invitation_id}/responder/', {'acao': 'aceitar'}, format='json'
        )
        self.assertEqual(accepted.status_code, 200, accepted.data)
        repeated = self.client.post(
            f'/api/convites/{invitation_id}/responder/', {'acao': 'recusar'}, format='json'
        )
        self.assertEqual(repeated.status_code, 400)
        self.assertEqual(self.client.patch(f'/api/convites/{invitation_id}/', {'cargo': 'owner'}).status_code, 405)

    def test_invites_cannot_assign_owner(self):
        project_id = self.create_project('Roles')
        response = self.client.post(
            '/api/convites/', {'projeto': project_id, 'usuario': self.guest.id, 'cargo': 'owner'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
