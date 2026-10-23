from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


class ProjetoTarefaSecurityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@email.com', password='senha123', name='Owner')
        self.admin = User.objects.create_user(email='admin@email.com', password='senha123', name='Admin')
        self.member = User.objects.create_user(email='member@email.com', password='senha123', name='Member')
        self.outro = User.objects.create_user(email='outro@email.com', password='senha123', name='Outro')
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

    def test_owner_equipe_automaticamente_e_endpoint_de_projetos_do_usuario(self):
        response = self.client.post(
            '/api/projetos/',
            {'nome': 'Projeto Alpha', 'descricao': 'Desc', 'cor': '#123456', 'icone': 'rocket-launch'},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['criador'], self.owner.id)
        self.assertEqual(response.data['icone'], 'rocket-launch')

        participantes = response.data['participantes']
        self.assertTrue(any(item['usuario'] == self.owner.id and item['cargo'] == 'owner' for item in participantes))

        response = self.client.get('/api/projetos/meus-projetos/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_administrador_pode_atualizar_projeto_mas_nao_deletar_e_nao_member_nao_pode(self):
        response = self.client.post(
            '/api/projetos/',
            {'nome': 'Projeto Beta', 'descricao': 'Desc', 'cor': '#123456'},
            format='json',
        )
        projeto_id = response.data['id']

        self.client.post(
            f'/api/projetos/{projeto_id}/adicionar-membro/',
            {'usuario': self.admin.id, 'cargo': 'admin'},
            format='json',
        )

        self.client.force_authenticate(user=self.admin)
        update = self.client.patch(
            f'/api/projetos/{projeto_id}/',
            {'descricao': 'Atualizado pelo admin'},
            format='json',
        )
        self.assertEqual(update.status_code, 200)

        delete_response = self.client.delete(f'/api/projetos/{projeto_id}/')
        self.assertEqual(delete_response.status_code, 403)

        self.client.force_authenticate(user=self.outro)
        forbidden = self.client.patch(
            f'/api/projetos/{projeto_id}/',
            {'descricao': 'Sem acesso'},
            format='json',
        )
        self.assertEqual(forbidden.status_code, 403)

    def test_tarefa_somente_para_membros_do_projeto(self):
        response = self.client.post(
            '/api/projetos/',
            {'nome': 'Projeto Tarefa', 'descricao': 'Desc', 'cor': '#abcdef'},
            format='json',
        )
        projeto_id = response.data['id']

        self.client.post(
            f'/api/projetos/{projeto_id}/adicionar-membro/',
            {'usuario': self.member.id, 'cargo': 'admin'},
            format='json',
        )

        self.client.force_authenticate(user=self.member)
        create_response = self.client.post(
            '/api/tarefas/',
            {'projeto': projeto_id, 'titulo': 'Implementar login', 'descricao': 'Teste', 'prioridade': 'alta'},
            format='json',
        )
        self.assertEqual(create_response.status_code, 201)
        tarefa_id = create_response.data['id']

        self.client.force_authenticate(user=self.outro)
        update_response = self.client.patch(
            f'/api/tarefas/{tarefa_id}/',
            {'titulo': 'Mudou de nome'},
            format='json',
        )
        self.assertEqual(update_response.status_code, 403)

    def test_fluxo_de_convite_aceito(self):
        response = self.client.post(
            '/api/projetos/',
            {'nome': 'Projeto Convite', 'descricao': 'Desc', 'cor': '#abcdef'},
            format='json',
        )
        projeto_id = response.data['id']

        convite_response = self.client.post(
            '/api/convites/',
            {'projeto': projeto_id, 'usuario': self.member.id, 'cargo': 'admin'},
            format='json',
        )
        self.assertEqual(convite_response.status_code, 201)
        convite_id = convite_response.data['id']

        self.client.force_authenticate(user=self.member)
        resposta = self.client.post(
            f'/api/convites/{convite_id}/responder/',
            {'acao': 'aceitar'},
            format='json',
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data['status'], 'aceito')
        self.assertTrue(
            self.client.get('/api/projetos/meus-projetos/').data[0]['participantes']
            and any(
                item['usuario'] == self.member.id
                for item in self.client.get('/api/projetos/meus-projetos/').data[0]['participantes']
            )
        )
