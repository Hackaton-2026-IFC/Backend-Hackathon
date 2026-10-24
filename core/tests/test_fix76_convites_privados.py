from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import ConviteProjeto, Projeto, ProjetoMembro

User = get_user_model()


class ConvitesPrivadosTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner76@example.com', password='TestPass123!')
        self.alice = User.objects.create_user(email='alice76@example.com', password='TestPass123!')
        self.bob = User.objects.create_user(email='bob76@example.com', password='TestPass123!')
        self.other = User.objects.create_user(email='other76@example.com', password='TestPass123!')
        self.project = Projeto.objects.create(nome='Projeto confidencial', criador=self.owner)
        for user, role in [(self.owner, 'owner'), (self.other, 'admin')]:
            ProjetoMembro.objects.create(projeto=self.project, usuario=user, cargo=role)
        self.alice_invite = ConviteProjeto.objects.create(
            projeto=self.project, usuario=self.alice, enviado_por=self.owner, cargo='member'
        )
        self.bob_invite = ConviteProjeto.objects.create(
            projeto=self.project, usuario=self.bob, enviado_por=self.owner, cargo='member'
        )
        self.client = APIClient()

    def _login(self, user):
        self.client.force_authenticate(user=user)

    @staticmethod
    def _results(response):
        data = response.data
        return data['results'] if isinstance(data, dict) and 'results' in data else data

    def test_recipient_sees_only_their_own_invites(self):
        self._login(self.alice)
        response = self.client.get('/api/convites/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['id'] for row in self._results(response)], [self.alice_invite.pk])

    def test_owner_and_admin_do_not_see_other_peoples_invites(self):
        for user in (self.owner, self.other):
            with self.subTest(user=user.email):
                self._login(user)
                response = self.client.get('/api/convites/')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(self._results(response), [])

    def test_query_params_cannot_override_recipient_filter(self):
        self._login(self.alice)
        response = self.client.get(f'/api/convites/?usuario={self.bob.pk}&projeto={self.project.pk}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._results(response), [])

    def test_detail_of_another_users_invite_is_not_accessible(self):
        self._login(self.alice)
        response = self.client.get(f'/api/convites/{self.bob_invite.pk}/')
        self.assertEqual(response.status_code, 404)

    def test_other_users_cannot_answer_invite(self):
        self._login(self.other)
        response = self.client.post(
            f'/api/convites/{self.alice_invite.pk}/responder/',
            {'acao': 'aceitar'}, format='json',
        )
        self.assertEqual(response.status_code, 404)
        self.alice_invite.refresh_from_db()
        self.assertEqual(self.alice_invite.status, 'pendente')

    def test_recipient_can_accept_and_become_project_member(self):
        self._login(self.alice)
        response = self.client.post(
            f'/api/convites/{self.alice_invite.pk}/responder/',
            {'acao': 'aceitar'}, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ProjetoMembro.objects.filter(projeto=self.project, usuario=self.alice).exists())

    def test_owner_still_can_create_invites(self):
        self._login(self.owner)
        new_user = User.objects.create_user(email='new76@example.com', password='TestPass123!')
        response = self.client.post('/api/convites/', {
            'projeto': self.project.pk, 'usuario': new_user.pk, 'cargo': 'member',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ConviteProjeto.objects.get(usuario=new_user).enviado_por, self.owner)

    def test_anonymous_user_cannot_list_invites(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/convites/')
        self.assertEqual(response.status_code, 401)
