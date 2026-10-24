from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Categoria, ProjetoMembro

User = get_user_model()


class FiltrosListagemTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='filtros-autor@example.com', password='SenhaForte123',
            name='Maria Souza', username='marias',
        )
        self.other = User.objects.create_user(
            email='filtros-externo@example.com', password='SenhaForte123',
            name='Externo', username='externo',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.projeto = self.client.post('/api/projetos/', {
            'nome': 'Projeto Alfa', 'descricao': 'Controle de pagamentos',
            'status': 'planejado',
        }, format='json').data['id']
        self.projeto2 = self.client.post('/api/projetos/', {
            'nome': 'Projeto Beta', 'descricao': 'Gestão de biblioteca',
            'status': 'em_andamento',
        }, format='json').data['id']
        self.tarefa1 = self.client.post('/api/tarefas/', {
            'projeto': self.projeto, 'titulo': 'API pagamento',
            'status': 'planejado', 'prioridade': 'alta',
        }, format='json').data['id']
        self.tarefa2 = self.client.post('/api/tarefas/', {
            'projeto': self.projeto2, 'titulo': 'Criar telas',
            'status': 'em_andamento', 'prioridade': 'baixa',
        }, format='json').data['id']
        self.micro = self.client.post('/api/microtarefas/', {
            'tarefa': self.tarefa1, 'titulo': 'Criar endpoint',
            'ordem': 1,
        }, format='json').data['id']
        self.recurso = self.client.post(f'/api/projetos/{self.projeto}/recursos/', {
            'titulo': 'Pasta Drive', 'tipo': 'pasta',
            'url': 'https://drive.google.com/',
        }, format='json').data['id']
        self.recurso2 = self.client.post(f'/api/projetos/{self.projeto2}/recursos/', {
            'titulo': 'Repositório GitHub', 'tipo': 'repositorio',
            'url': 'https://github.com/',
        }, format='json').data['id']
        self.cat1 = Categoria.objects.create(descricao='Backend')
        self.cat2 = Categoria.objects.create(descricao='Frontend')

        self.client.force_authenticate(user=self.other)
        self.outro_projeto = self.client.post('/api/projetos/', {
            'nome': 'Projeto Privado', 'status': 'concluido',
        }, format='json').data['id']
        self.outro_tarefa = self.client.post('/api/tarefas/', {
            'projeto': self.outro_projeto, 'titulo': 'API privada',
        }, format='json').data['id']
        self.client.force_authenticate(user=self.user)

    def ids(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, getattr(response, 'data', None))
        payload = response.data
        rows = payload['results'] if isinstance(payload, dict) and 'results' in payload else payload
        return [item['id'] for item in rows]

    def test_projetos_filtro_busca_ordenacao(self):
        self.assertEqual(self.ids('/api/projetos/?status=planejado'), [self.projeto])
        self.assertEqual(self.ids('/api/projetos/?search=biblioteca'), [self.projeto2])
        self.assertEqual(self.ids('/api/projetos/?ordering=nome'), [self.projeto, self.projeto2])
        self.assertEqual(self.ids('/api/projetos/?ordering=-nome'), [self.projeto2, self.projeto])
        self.assertEqual(self.ids('/api/projetos/meus-projetos/?status=planejado'), [self.projeto])
        self.assertEqual(self.ids('/api/projetos/?status=concluido'), [])

    def test_tarefas_combinadas_e_sem_vazar_dados(self):
        url = f'/api/tarefas/?projeto={self.projeto}&prioridade=alta&search=API'
        self.assertEqual(self.ids(url), [self.tarefa1])
        self.assertEqual(self.ids('/api/tarefas/?status=em_andamento'), [self.tarefa2])
        self.assertEqual(self.ids('/api/tarefas/?search=privada'), [])
        self.assertEqual(self.ids('/api/tarefas/?ordering=titulo'), [self.tarefa1, self.tarefa2])
        self.assertEqual(self.ids(f'/api/tarefas/?projeto={self.outro_projeto}'), [])

    def test_microtarefas_busca_filtro_e_ordenacao(self):
        self.assertEqual(self.ids(f'/api/microtarefas/?tarefa={self.tarefa1}&search=endpoint'), [self.micro])
        self.assertEqual(self.ids(f'/api/microtarefas/?tarefa__projeto={self.projeto2}'), [])
        self.assertEqual(self.ids('/api/microtarefas/?ordering=ordem'), [self.micro])

    def test_recursos_filtro_busca_e_ordenacao(self):
        self.assertEqual(self.ids(f'/api/recursos/?projeto={self.projeto}&tipo=pasta'), [self.recurso])
        self.assertEqual(self.ids('/api/recursos/?search=github'), [self.recurso2])
        self.assertEqual(self.ids('/api/recursos/?ordering=titulo'), [self.recurso, self.recurso2])

    def test_usuarios_pesquisa_e_ordenacao(self):
        resultado = self.ids('/api/usuarios/?search=maria')
        self.assertIn(self.user.id, resultado)
        self.assertNotIn(self.other.id, resultado)
        self.assertEqual(self.ids('/api/usuarios/?username=marias'), [self.user.id])

    def test_categorias_filtro_busca_e_ordenacao(self):
        self.assertEqual(self.ids('/api/categorias/?descricao=Backend'), [self.cat1.id])
        self.assertEqual(self.ids('/api/categorias/?search=front'), [self.cat2.id])
        self.assertEqual(self.ids('/api/categorias/?ordering=-descricao'), [self.cat2.id, self.cat1.id])

    def test_convites_filtro_isolamento(self):
        invite = self.client.post('/api/convites/', {
            'projeto': self.projeto, 'usuario': self.other.id, 'cargo': 'member',
        }, format='json')
        self.assertEqual(invite.status_code, 201, invite.data)
        cid = invite.data['id']
        # O remetente não pode visualizar convites destinados a outras pessoas.
        self.assertEqual(self.ids(f'/api/convites/?projeto={self.projeto}&status=pendente'), [])
        self.assertEqual(self.ids('/api/convites/?search=Alfa'), [])
        self.assertEqual(self.ids(f'/api/convites/?projeto={self.outro_projeto}'), [])
        # O destinatário conserva os filtros de projeto, status e busca.
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.ids(f'/api/convites/?projeto={self.projeto}&status=pendente'), [cid])
        self.assertEqual(self.ids('/api/convites/?search=Alfa'), [cid])
