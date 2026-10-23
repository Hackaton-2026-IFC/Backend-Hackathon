from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from core.models import ProjetoFixado

User = get_user_model()


class ProjetoFixadoTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(email='pin-alice@example.com', password='SenhaForte123')
        self.bob = User.objects.create_user(email='pin-bob@example.com', password='SenhaForte123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.alice)
        self.ids = []
        for nome in ('Primeiro', 'Segundo', 'Terceiro'):
            response = self.client.post('/api/projetos/', {'nome': nome}, format='json')
            self.assertEqual(response.status_code, 201, response.data)
            self.ids.append(response.data['id'])

    def listar(self):
        return self.client.get('/api/projetos/').data['results']

    def test_usuario_pode_fixar_varios_projetos_e_priorizar_lista(self):
        for pid in self.ids[:2]:
            res = self.client.post(f'/api/projetos/{pid}/fixar/')
            self.assertEqual(res.status_code, 200, res.data)
            self.assertEqual(res.data['fixado'], True)
        lista = self.listar()
        self.assertEqual({x['id'] for x in lista[:2]}, set(self.ids[:2]))
        self.assertTrue(all(x['fixado'] for x in lista[:2]))
        self.assertEqual(ProjetoFixado.objects.filter(usuario=self.alice).count(), 2)
        self.client.post(f'/api/projetos/{self.ids[0]}/fixar/')
        self.assertEqual(ProjetoFixado.objects.filter(usuario=self.alice).count(), 2)

    def test_fixacao_e_individual_por_usuario(self):
        self.client.post(f'/api/projetos/{self.ids[0]}/fixar/')
        self.client.post(
            f'/api/projetos/{self.ids[0]}/adicionar-membro/',
            {'usuario': self.bob.id, 'cargo': 'member'},
            format='json',
        )
        self.client.force_authenticate(user=self.bob)
        resposta = self.client.get(f'/api/projetos/{self.ids[0]}/')
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(resposta.data['fixado'])
        self.client.post(f'/api/projetos/{self.ids[0]}/fixar/')
        self.client.force_authenticate(user=self.alice)
        self.client.delete(f'/api/projetos/{self.ids[0]}/fixar/')
        self.assertFalse(self.client.get(f'/api/projetos/{self.ids[0]}/').data['fixado'])
        self.client.force_authenticate(user=self.bob)
        self.assertTrue(self.client.get(f'/api/projetos/{self.ids[0]}/').data['fixado'])

    def test_nao_pode_fixar_projeto_sem_participar(self):
        self.client.force_authenticate(user=self.bob)
        res = self.client.post(f'/api/projetos/{self.ids[1]}/fixar/')
        self.assertEqual(res.status_code, 403)
        self.assertEqual(ProjetoFixado.objects.count(), 0)

    def test_desafixar_e_idempotente(self):
        url = f'/api/projetos/{self.ids[0]}/fixar/'
        self.assertEqual(self.client.delete(url).status_code, 200)
        self.client.post(url)
        self.assertEqual(self.client.delete(url).data['fixado'], False)
        self.assertEqual(ProjetoFixado.objects.count(), 0)
