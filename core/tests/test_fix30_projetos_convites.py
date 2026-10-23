from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import ConviteProjeto, ProjetoMembro
from core.views.convides import ConviteProjetoViewSet

User = get_user_model()


class DetalhesProjetoConvitesTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='fix30-owner@example.com', name='Proprietário', username='owner',
            password='SenhaForte123',
        )
        self.member = User.objects.create_user(
            email='fix30-member@example.com', name='Participante', username='member',
            password='SenhaForte123',
        )
        self.outsider = User.objects.create_user(
            email='fix30-outsider@example.com', password='SenhaForte123',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        response = self.client.post('/api/projetos/', {'nome': 'FIX-30'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.pid = response.data['id']
        ProjetoMembro.objects.create(projeto_id=self.pid, usuario=self.member, cargo='member')

    def test_detalhe_projeto_traz_perfil_criador_e_participantes(self):
        resp = self.client.get(f'/api/projetos/{self.pid}/')
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['criador'], self.owner.id)
        self.assertEqual(resp.data['criador_detalhes']['name'], 'Proprietário')
        self.assertIn('profile_image', resp.data['criador_detalhes'])
        participantes = resp.data['participantes']
        self.assertEqual(len(participantes), 2)
        membro = next(m for m in participantes if m['usuario'] == self.member.id)
        self.assertEqual(membro['usuario_detalhes']['name'], 'Participante')
        self.assertEqual(membro['usuario_detalhes']['username'], 'member')
        self.assertIn('profile_image', membro['usuario_detalhes'])
        self.assertNotIn('email', membro['usuario_detalhes'])

    def test_listagem_membros_contem_perfil(self):
        resp = self.client.get(f'/api/projetos/{self.pid}/membros/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('usuario_detalhes', resp.data[0])

    def test_nao_membro_nao_ve_perfis_projeto(self):
        self.client.force_authenticate(user=self.outsider)
        self.assertEqual(self.client.get(f'/api/projetos/{self.pid}/').status_code, 403)
        self.assertEqual(self.client.get(f'/api/projetos/{self.pid}/membros/').status_code, 403)

    def test_aceitar_convite_e_idempotencia(self):
        self.client.force_authenticate(user=self.owner)
        convite = self.client.post('/api/convites/', {
            'projeto': self.pid, 'usuario': self.outsider.id, 'cargo': 'member',
        }, format='json')
        self.assertEqual(convite.status_code, 201, convite.data)
        self.client.force_authenticate(user=self.outsider)
        res = self.client.post(
            f"/api/convites/{convite.data['id']}/responder/",
            {'acao': 'aceitar'}, format='json',
        )
        self.assertEqual(res.status_code, 200, res.data)
        self.assertTrue(ProjetoMembro.objects.filter(projeto_id=self.pid, usuario=self.outsider).exists())
        novamente = self.client.post(
            f"/api/convites/{convite.data['id']}/responder/",
            {'acao': 'aceitar'}, format='json',
        )
        self.assertEqual(novamente.status_code, 400)

    def test_responder_usa_bloqueio_sem_distinct_na_query_externa(self):
        self.client.force_authenticate(user=self.outsider)
        view = ConviteProjetoViewSet()
        view.action = 'responder'
        view.request = type('Request', (), {'user': self.outsider})()
        qs = view.get_queryset()
        self.assertTrue(qs.query.select_for_update)
        self.assertFalse(qs.query.distinct)
        self.assertEqual(qs.query.alias_map.get('core_projetomembro'), None)

    def test_nao_pode_responder_convite_de_outra_pessoa(self):
        self.client.force_authenticate(user=self.owner)
        convite = self.client.post('/api/convites/', {
            'projeto': self.pid, 'usuario': self.outsider.id, 'cargo': 'member',
        }, format='json')
        self.assertEqual(convite.status_code, 201, convite.data)
        resposta = self.client.post(
            f"/api/convites/{convite.data['id']}/responder/",
            {'acao': 'aceitar'}, format='json',
        )
        self.assertEqual(resposta.status_code, 403)
        self.assertFalse(ProjetoMembro.objects.filter(projeto_id=self.pid, usuario=self.outsider).exists())
