from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Nota, Projeto, ProjetoMembro

User = get_user_model()


class MuralCompartilhadoTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner73@example.com', password='TestPass123!', name='Dona')
        self.member = User.objects.create_user(email='member73@example.com', password='TestPass123!', name='Membro')
        self.outsider = User.objects.create_user(email='outsider73@example.com', password='TestPass123!', name='Visitante')
        self.project_a = Projeto.objects.create(nome='Projeto A', criador=self.owner)
        self.project_b = Projeto.objects.create(nome='Projeto B', criador=self.owner)
        for project in (self.project_a, self.project_b):
            ProjetoMembro.objects.create(projeto=project, usuario=self.owner, cargo='owner')
        ProjetoMembro.objects.create(projeto=self.project_a, usuario=self.member, cargo='member')
        self.personal_note = Nota.objects.create(usuario=self.owner, titulo='Rascunho particular')
        self.note_a = Nota.objects.create(usuario=self.owner, projeto=self.project_a, titulo='Ideia A')
        self.note_b = Nota.objects.create(usuario=self.owner, projeto=self.project_b, titulo='Ideia B')
        self.client = APIClient()

    def login(self, user):
        self.client.force_authenticate(user=user)

    @staticmethod
    def notes(response):
        return response.data['results']

    def test_membro_le_mural_do_projeto_e_nao_ve_notas_privadas(self):
        self.login(self.member)
        r = self.client.get(f'/api/notas/?projeto={self.project_a.pk}')
        self.assertEqual(r.status_code, 200)
        self.assertEqual([n['id'] for n in self.notes(r)], [self.note_a.pk])
        self.assertEqual(self.notes(r)[0]['usuario_nome'], 'Dona')
        self.assertEqual(self.client.get(f'/api/notas/{self.note_a.pk}/').status_code, 200)
        self.assertEqual(self.client.get(f'/api/notas/{self.personal_note.pk}/').status_code, 404)
        self.assertEqual(self.client.get(f'/api/notas/{self.note_b.pk}/').status_code, 404)
        self.assertEqual(self.notes(self.client.get('/api/notas/')), [])

    def test_todos_membros_podem_publicar_com_texto_link_e_tags(self):
        self.login(self.member)
        response = self.client.post('/api/notas/', {
            'projeto': self.project_a.pk, 'titulo': 'Novo layout',
            'conteudo': 'Ver o rascunho', 'link': 'https://example.org/layout',
            'etiquetas': ['ideia'],
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['usuario'], self.member.pk)
        self.assertEqual(response.data['usuario_nome'], 'Membro')
        self.login(self.owner)
        r = self.client.get(f'/api/notas/?projeto={self.project_a.pk}&search=layout')
        self.assertEqual([n['id'] for n in self.notes(r)], [response.data['id']])
        self.assertEqual(len(self.notes(self.client.get('/api/notas/'))), 3)

    def test_autoria_protege_edicao_arquivamento_e_exclusao(self):
        self.login(self.member)
        for data in ({'titulo': 'Invadida'}, {'fixada': True}, {'arquivada': True}):
            self.assertEqual(
                self.client.patch(f'/api/notas/{self.note_a.pk}/', data, format='json').status_code,
                403,
            )
        self.assertEqual(self.client.delete(f'/api/notas/{self.note_a.pk}/').status_code, 403)
        self.note_a.refresh_from_db()
        self.assertEqual(self.note_a.titulo, 'Ideia A')
        self.assertFalse(self.note_a.arquivada)
        created = self.client.post('/api/notas/', {'projeto': self.project_a.pk, 'titulo': 'Minha ideia'}, format='json')
        self.assertEqual(created.status_code, 201)
        self.assertEqual(
            self.client.patch(f'/api/notas/{created.data["id"]}/', {'titulo': 'Atualizada'}, format='json').status_code,
            200,
        )
        self.assertEqual(self.client.delete(f'/api/notas/{created.data["id"]}/').status_code, 204)

    def test_isolamento_entre_projetos_e_acesso_anonimo(self):
        self.login(self.member)
        self.assertEqual(self.notes(self.client.get(f'/api/notas/?projeto={self.project_b.pk}')), [])
        self.assertEqual(self.notes(self.client.get(f'/api/notas/?projeto={self.project_a.pk}&search=Ideia%20B')), [])
        self.assertEqual(self.client.post('/api/notas/', {'projeto': self.project_b.pk, 'titulo': 'Invasao'}, format='json').status_code, 400)
        self.login(self.outsider)
        self.assertEqual(self.notes(self.client.get(f'/api/notas/?projeto={self.project_a.pk}')), [])
        self.assertEqual(self.client.get(f'/api/notas/{self.note_a.pk}/').status_code, 404)
        self.assertEqual(self.client.delete(f'/api/notas/{self.note_a.pk}/').status_code, 404)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get('/api/notas/').status_code, 401)

    def test_ao_sair_do_projeto_perde_acesso_mesmo_sendo_autor(self):
        self.login(self.member)
        created = self.client.post('/api/notas/', {'projeto': self.project_a.pk, 'titulo': 'Minha antiga'}, format='json')
        self.assertEqual(created.status_code, 201)
        ProjetoMembro.objects.filter(projeto=self.project_a, usuario=self.member).delete()
        self.assertEqual(self.notes(self.client.get(f'/api/notas/?projeto={self.project_a.pk}')), [])
        self.assertEqual(self.client.get(f'/api/notas/{created.data["id"]}/').status_code, 404)
        self.assertEqual(self.client.patch(f'/api/notas/{created.data["id"]}/', {'titulo': 'X'}, format='json').status_code, 404)
