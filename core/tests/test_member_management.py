from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Projeto, ProjetoMembro

User = get_user_model()


class MemberManagementTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner3@example.com', password='12345678')
        self.admin = User.objects.create_user(email='admin3@example.com', password='12345678')
        self.member = User.objects.create_user(email='member3@example.com', password='12345678')
        self.other = User.objects.create_user(email='other3@example.com', password='12345678')
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        res = self.client.post('/api/projetos/', {'nome': 'Projeto membros'}, format='json')
        self.assertEqual(res.status_code, 201, res.data)
        self.pid = res.data['id']
        for user, cargo in [(self.admin, 'admin'), (self.member, 'member')]:
            res = self.client.post(
                f'/api/projetos/{self.pid}/adicionar-membro/',
                {'usuario': user.id, 'cargo': cargo}, format='json',
            )
            self.assertEqual(res.status_code, 201, res.data)

    def auth(self, user):
        self.client.force_authenticate(user=user)

    def test_member_list_and_member_cannot_edit_project(self):
        res = self.client.get(f'/api/projetos/{self.pid}/membros/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 3)
        self.auth(self.member)
        self.assertEqual(
            self.client.patch(f'/api/projetos/{self.pid}/', {'nome': 'Invasão'}, format='json').status_code,
            403,
        )
        self.auth(self.other)
        self.assertEqual(self.client.get(f'/api/projetos/{self.pid}/membros/').status_code, 403)

    def test_only_owner_changes_roles(self):
        endpoint = f'/api/projetos/{self.pid}/membros/{self.member.id}/cargo/'
        self.auth(self.admin)
        self.assertEqual(self.client.patch(endpoint, {'cargo': 'admin'}, format='json').status_code, 403)
        self.auth(self.owner)
        self.assertEqual(self.client.patch(endpoint, {'cargo': 'owner'}, format='json').status_code, 400)
        self.assertEqual(self.client.patch(endpoint, {'cargo': 'admin'}, format='json').status_code, 200)
        self.assertTrue(ProjetoMembro.objects.filter(projeto_id=self.pid, usuario=self.member, cargo='admin').exists())

    def test_member_can_leave_and_admin_cannot_remove_owner(self):
        self.auth(self.admin)
        url = f'/api/projetos/{self.pid}/membros/{self.owner.id}/'
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.auth(self.member)
        url = f'/api/projetos/{self.pid}/membros/{self.member.id}/'
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertFalse(ProjetoMembro.objects.filter(projeto_id=self.pid, usuario=self.member).exists())

    def test_owner_transfer(self):
        res = self.client.post(
            f'/api/projetos/{self.pid}/transferir-propriedade/',
            {'usuario': self.admin.id}, format='json',
        )
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(Projeto.objects.get(pk=self.pid).criador_id, self.admin.id)
        self.assertEqual(ProjetoMembro.objects.filter(projeto_id=self.pid, cargo='owner').count(), 1)
        self.assertEqual(
            ProjetoMembro.objects.get(projeto_id=self.pid, usuario=self.owner).cargo, 'admin'
        )
        self.assertEqual(self.client.delete(f'/api/projetos/{self.pid}/').status_code, 403)
        self.auth(self.admin)
        self.assertEqual(self.client.delete(f'/api/projetos/{self.pid}/').status_code, 204)

    def test_admin_can_only_invite_members(self):
        self.auth(self.admin)
        for cargo, expected in [('owner', 400), ('admin', 403), ('member', 201)]:
            res = self.client.post(
                '/api/convites/',
                {'projeto': self.pid, 'usuario': self.other.id, 'cargo': cargo}, format='json',
            )
            self.assertEqual(res.status_code, expected, res.data)
