from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import ConviteProjeto, Projeto, ProjetoMembro

User = get_user_model()


class ReconviteAposSaidaTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner-reconvite@example.com', password='TestPass123!')
        self.guest = User.objects.create_user(email='guest-reconvite@example.com', password='TestPass123!')
        self.project = Projeto.objects.create(nome='Projeto Reconvite', criador=self.owner)
        ProjetoMembro.objects.create(projeto=self.project, usuario=self.owner, cargo='owner')
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

    def invite(self):
        return self.client.post('/api/convites/', {
            'projeto': self.project.pk, 'usuario': self.guest.pk, 'cargo': 'member',
        }, format='json')

    def test_accepted_invite_can_be_sent_again_after_leaving(self):
        first = self.invite()
        self.assertEqual(first.status_code, 201, first.data)

        self.client.force_authenticate(user=self.guest)
        answer = self.client.post(
            f"/api/convites/{first.data['id']}/responder/",
            {'acao': 'aceitar'}, format='json',
        )
        self.assertEqual(answer.status_code, 200, answer.data)
        leave = self.client.delete(
            f'/api/projetos/{self.project.pk}/membros/{self.guest.pk}/'
        )
        self.assertEqual(leave.status_code, 204)
        self.assertFalse(ProjetoMembro.objects.filter(projeto=self.project, usuario=self.guest).exists())

        self.client.force_authenticate(user=self.owner)
        second = self.invite()
        self.assertEqual(second.status_code, 201, second.data)
        self.assertNotEqual(first.data['id'], second.data['id'])
        self.assertEqual(ConviteProjeto.objects.filter(projeto=self.project, usuario=self.guest).count(), 2)

        self.client.force_authenticate(user=self.guest)
        accepted_again = self.client.post(
            f"/api/convites/{second.data['id']}/responder/",
            {'acao': 'aceitar'}, format='json',
        )
        self.assertEqual(accepted_again.status_code, 200, accepted_again.data)
        self.assertTrue(ProjetoMembro.objects.filter(projeto=self.project, usuario=self.guest).exists())

    def test_declined_invite_can_be_sent_again(self):
        first = self.invite()
        self.assertEqual(first.status_code, 201, first.data)
        self.client.force_authenticate(user=self.guest)
        answer = self.client.post(
            f"/api/convites/{first.data['id']}/responder/",
            {'acao': 'recusar'}, format='json',
        )
        self.assertEqual(answer.status_code, 200, answer.data)

        self.client.force_authenticate(user=self.owner)
        second = self.invite()
        self.assertEqual(second.status_code, 201, second.data)
        self.assertEqual(ConviteProjeto.objects.filter(projeto=self.project, usuario=self.guest).count(), 2)

    def test_duplicate_pending_invite_returns_400(self):
        first = self.invite()
        self.assertEqual(first.status_code, 201, first.data)
        duplicate = self.invite()
        self.assertEqual(duplicate.status_code, 400, duplicate.data)
        self.assertIn('usuario', duplicate.data)
        self.assertEqual(ConviteProjeto.objects.filter(projeto=self.project, usuario=self.guest).count(), 1)

    def test_cannot_invite_existing_member_even_after_previous_invite(self):
        invite = self.invite()
        self.assertEqual(invite.status_code, 201, invite.data)
        self.client.force_authenticate(user=self.guest)
        self.assertEqual(self.client.post(
            f"/api/convites/{invite.data['id']}/responder/",
            {'acao': 'aceitar'}, format='json',
        ).status_code, 200)
        self.client.force_authenticate(user=self.owner)
        repeated = self.invite()
        self.assertEqual(repeated.status_code, 400, repeated.data)
        self.assertIn('usuario', repeated.data)
