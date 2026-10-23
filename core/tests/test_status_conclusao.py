from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


class StatusConclusaoConsistencyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='status-sync@example.com', password='SenhaForte123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        projeto = self.client.post('/api/projetos/', {'nome': 'Status sync'}, format='json')
        self.assertEqual(projeto.status_code, 201, projeto.data)
        self.projeto = projeto.data['id']

    def test_criar_concluida_sincroniza_booleano(self):
        resposta = self.client.post(
            '/api/tarefas/',
            {'projeto': self.projeto, 'titulo': 'Finalizada', 'status': 'concluido'},
            format='json',
        )
        self.assertEqual(resposta.status_code, 201, resposta.data)
        self.assertEqual(resposta.data['status'], 'concluido')
        self.assertTrue(resposta.data['concluida'])
        detalhe = self.client.get(f"/api/tarefas/{resposta.data['id']}/")
        self.assertTrue(detalhe.data['concluida'])

    def test_criar_nao_concluida_mantem_booleano_false(self):
        for status in ('planejado', 'em_andamento'):
            with self.subTest(status=status):
                resposta = self.client.post(
                    '/api/tarefas/',
                    {'projeto': self.projeto, 'titulo': status, 'status': status},
                    format='json',
                )
                self.assertEqual(resposta.status_code, 201, resposta.data)
                self.assertFalse(resposta.data['concluida'])

    def test_patch_status_continua_sincronizado(self):
        criada = self.client.post(
            '/api/tarefas/',
            {'projeto': self.projeto, 'titulo': 'Transicao'},
            format='json',
        )
        pk = criada.data['id']
        concluida = self.client.patch(f'/api/tarefas/{pk}/', {'status': 'concluido'}, format='json')
        self.assertEqual(concluida.status_code, 200, concluida.data)
        self.assertTrue(concluida.data['concluida'])
        reaberta = self.client.patch(f'/api/tarefas/{pk}/', {'status': 'em_andamento'}, format='json')
        self.assertEqual(reaberta.status_code, 200, reaberta.data)
        self.assertFalse(reaberta.data['concluida'])
