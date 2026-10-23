from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


class MicrotarefaSequenciaParcialTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            email='fix39@example.com', password='SenhaForte123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.usuario)
        projeto = self.client.post('/api/projetos/', {'nome': 'Roadmap'}, format='json')
        self.assertEqual(projeto.status_code, 201, projeto.data)
        tarefa = self.client.post(
            '/api/tarefas/',
            {'projeto': projeto.data['id'], 'titulo': 'Entrega'},
            format='json',
        )
        self.assertEqual(tarefa.status_code, 201, tarefa.data)
        self.tarefa = tarefa.data['id']

    def test_roadmap_parcial_permanece_editavel_sem_pular_ordem(self):
        ids = []
        for ordem in range(1, 4):
            response = self.client.post(
                '/api/microtarefas/',
                {'tarefa': self.tarefa, 'titulo': f'Etapa {ordem}', 'ordem': ordem},
                format='json',
            )
            self.assertEqual(response.status_code, 201, response.data)
            ids.append(response.data['id'])

        primeira = self.client.patch(
            f'/api/microtarefas/{ids[0]}/',
            {'concluida': True}, format='json',
        )
        self.assertEqual(primeira.status_code, 200, primeira.data)

        # [concluida, pendente, pendente] e um estado valido.
        # Editar a etapa 3 sem conclui-la nao deve dar erro.
        terceira = self.client.patch(
            f'/api/microtarefas/{ids[2]}/',
            {'descricao': 'Atualizada'}, format='json',
        )
        self.assertEqual(terceira.status_code, 200, terceira.data)

        # Ainda nao e permitido saltar a etapa 2.
        salto = self.client.patch(
            f'/api/microtarefas/{ids[2]}/',
            {'concluida': True}, format='json',
        )
        self.assertEqual(salto.status_code, 400, salto.data)

        segunda = self.client.patch(
            f'/api/microtarefas/{ids[1]}/',
            {'concluida': True}, format='json',
        )
        self.assertEqual(segunda.status_code, 200, segunda.data)
        terceira = self.client.patch(
            f'/api/microtarefas/{ids[2]}/',
            {'concluida': True}, format='json',
        )
        self.assertEqual(terceira.status_code, 200, terceira.data)
