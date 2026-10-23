from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Nota

User = get_user_model()


class NotaKeepTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='keep-owner@test.com', password='12345678')
        self.outro = User.objects.create_user(email='keep-outro@test.com', password='12345678')
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        self.projeto = self.client.post('/api/projetos/', {'nome': 'Projeto Keep'}, format='json').data['id']

    def test_crud_keep_e_isolamento(self):
        created = self.client.post(
            '/api/notas/',
            {
                'projeto': self.projeto,
                'titulo': 'Ideia',
                'conteudo': 'Transformar ideia em tarefas',
                'cor': '#AABBCC',
                'fixada': True,
                'etiquetas': ['hackathon', 'ideia'],
            },
            format='json',
        )
        self.assertEqual(created.status_code, 201)
        self.assertTrue(created.data['fixada'])
        self.assertEqual(created.data['cor'], '#AABBCC')

        note_id = created.data['id']
        self.assertEqual(self.client.get('/api/notas/?search=Transformar').data['count'], 1)
        self.assertEqual(
            self.client.patch(f'/api/notas/{note_id}/', {'arquivada': True}, format='json').status_code,
            200,
        )

        self.client.force_authenticate(user=self.outro)
        self.assertEqual(self.client.get('/api/notas/').data['count'], 0)
        self.assertEqual(self.client.get(f'/api/notas/{note_id}/').status_code, 404)

    def test_nao_vincula_nota_a_projeto_alheio(self):
        self.client.force_authenticate(user=self.outro)
        projeto_alheio = self.client.post('/api/projetos/', {'nome': 'Outro'}, format='json').data['id']
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            '/api/notas/',
            {'projeto': projeto_alheio, 'titulo': 'Não pode'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Nota.objects.count(), 0)
