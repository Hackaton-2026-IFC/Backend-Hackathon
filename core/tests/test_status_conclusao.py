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
        self.assertIsNotNone(resposta.data['data_conclusao'])
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
                self.assertIsNone(resposta.data['data_conclusao'])

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
        self.assertIsNotNone(concluida.data['data_conclusao'])
        data_conclusao = concluida.data['data_conclusao']
        outra_edicao = self.client.patch(f'/api/tarefas/{pk}/', {'descricao': 'ajuste'}, format='json')
        self.assertEqual(outra_edicao.data['data_conclusao'], data_conclusao)
        reaberta = self.client.patch(f'/api/tarefas/{pk}/', {'status': 'em_andamento'}, format='json')
        self.assertEqual(reaberta.status_code, 200, reaberta.data)
        self.assertFalse(reaberta.data['concluida'])
        self.assertIsNone(reaberta.data['data_conclusao'])
        novamente = self.client.patch(f'/api/tarefas/{pk}/', {'status': 'concluido'}, format='json')
        self.assertIsNotNone(novamente.data['data_conclusao'])

    def test_fechamento_automatico_pelas_microtarefas_registra_data(self):
        criada = self.client.post(
            '/api/tarefas/',
            {'projeto': self.projeto, 'titulo': 'Checklist'},
            format='json',
        )
        tarefa_id = criada.data['id']
        etapa = self.client.post(
            '/api/microtarefas/',
            {'tarefa': tarefa_id, 'titulo': 'Última etapa', 'ordem': 1},
            format='json',
        )
        self.assertEqual(etapa.status_code, 201, etapa.data)
        finalizada = self.client.patch(
            f"/api/microtarefas/{etapa.data['id']}/",
            {'concluida': True},
            format='json',
        )
        self.assertEqual(finalizada.status_code, 200, finalizada.data)
        detalhe = self.client.get(f'/api/tarefas/{tarefa_id}/')
        self.assertEqual(detalhe.data['status'], 'concluido')
        self.assertIsNotNone(detalhe.data['data_conclusao'])
