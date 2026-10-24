from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Nota, NotaPreferencia, Projeto, ProjetoMembro

User = get_user_model()


class PreferenciasDoMuralTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner74@example.com', password='Pass123!', name='Owner')
        self.member = User.objects.create_user(email='member74@example.com', password='Pass123!', name='Member')
        self.outsider = User.objects.create_user(email='out74@example.com', password='Pass123!', name='Outsider')
        self.project = Projeto.objects.create(nome='Projeto A', criador=self.owner)
        self.other_project = Projeto.objects.create(nome='Projeto B', criador=self.owner)
        for project in (self.project, self.other_project):
            ProjetoMembro.objects.create(projeto=project, usuario=self.owner, cargo='owner')
        ProjetoMembro.objects.create(projeto=self.project, usuario=self.member, cargo='member')
        self.a = Nota.objects.create(projeto=self.project, usuario=self.owner, titulo='Ideia A')
        self.b = Nota.objects.create(projeto=self.project, usuario=self.member, titulo='Ideia B')
        self.c = Nota.objects.create(projeto=self.project, usuario=self.owner, titulo='Ideia C')
        self.secret = Nota.objects.create(usuario=self.owner, titulo='Pessoal')
        self.other_note = Nota.objects.create(projeto=self.other_project, usuario=self.owner, titulo='Outro')
        self.client = APIClient()

    def login(self, user):
        self.client.force_authenticate(user=user)

    def list_ids(self):
        result = self.client.get(f'/api/notas/?projeto={self.project.pk}&arquivada=false')
        self.assertEqual(result.status_code, 200)
        return result.data['results']

    def test_membros_fixam_qualquer_ideia_sem_compartilhar_fixacao(self):
        self.login(self.owner)
        response = self.client.patch(f'/api/notas/{self.b.pk}/preferencia/', {'fixada': True}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data['fixada'])
        self.assertEqual(self.list_ids()[0]['id'], self.b.pk)

        self.login(self.member)
        first = self.list_ids()
        self.assertFalse(next(n for n in first if n['id'] == self.b.pk)['fixada'])
        self.assertTrue(all(n['fixada'] is False for n in first))
        response = self.client.patch(f'/api/notas/{self.a.pk}/preferencia/', {'fixada': True}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.list_ids()[0]['id'], self.a.pk)
        self.login(self.owner)
        self.assertEqual(self.list_ids()[0]['id'], self.b.pk)
        self.assertFalse(next(n for n in self.list_ids() if n['id'] == self.a.pk)['fixada'])
        self.assertEqual(NotaPreferencia.objects.filter(nota=self.a).count(), 1)
        self.assertEqual(NotaPreferencia.objects.filter(nota=self.b).count(), 1)
        self.b.refresh_from_db()
        self.assertFalse(self.b.fixada)

    def test_ordem_individual_persistente_e_pins_sempre_primeiro(self):
        self.login(self.owner)
        ids = [self.c.pk, self.a.pk, self.b.pk]
        response = self.client.post('/api/notas/ordenar/', {'projeto': self.project.pk, 'ids': ids}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual([n['id'] for n in self.list_ids()], ids)
        self.login(self.member)
        self.assertNotEqual([n['id'] for n in self.list_ids()], ids)
        member_ids = [self.b.pk, self.a.pk, self.c.pk]
        self.assertEqual(self.client.post('/api/notas/ordenar/', {'projeto': self.project.pk, 'ids': member_ids}, format='json').status_code, 200)
        self.assertEqual([n['id'] for n in self.list_ids()], member_ids)
        self.login(self.owner)
        self.assertEqual([n['id'] for n in self.list_ids()], ids)
        self.client.patch(f'/api/notas/{self.b.pk}/preferencia/', {'fixada': True}, format='json')
        self.assertEqual([n['id'] for n in self.list_ids()], [self.b.pk, self.c.pk, self.a.pk])
        self.client.patch(f'/api/notas/{self.b.pk}/preferencia/', {'fixada': False}, format='json')
        self.assertEqual([n['id'] for n in self.list_ids()], ids)

    def test_ordem_rejeita_outro_projeto_duplicados_e_incompletos(self):
        self.login(self.member)
        for ids in ([self.a.pk, self.a.pk, self.c.pk], [self.a.pk], [self.a.pk, self.b.pk, self.other_note.pk]):
            r = self.client.post('/api/notas/ordenar/', {'projeto': self.project.pk, 'ids': ids}, format='json')
            self.assertEqual(r.status_code, 400, r.data)
        self.assertEqual(NotaPreferencia.objects.count(), 0)
        bad = self.client.patch(f'/api/notas/{self.secret.pk}/preferencia/', {'fixada': True}, format='json')
        self.assertEqual(bad.status_code, 404)
        self.assertEqual(self.client.post('/api/notas/ordenar/', {'projeto': self.other_project.pk, 'ids': [self.other_note.pk]}, format='json').status_code, 404)

    def test_notas_antigas_e_criacao_com_fixacao_continuam_funcionando(self):
        self.login(self.owner)
        r = self.client.post('/api/notas/', {'projeto': self.project.pk, 'titulo': 'Nova', 'fixada': True}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(r.data['fixada'])
        self.login(self.member)
        note = next(n for n in self.list_ids() if n['id'] == r.data['id'])
        self.assertFalse(note['fixada'])
        self.assertIsInstance(note['ordem'], int)
        self.login(self.owner)
        r = self.client.patch(f'/api/notas/{r.data["id"]}/', {'fixada': False}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertFalse(r.data['fixada'])

    def test_outsider_nao_pode_fixar_e_anonimo_nao_pode_ordenar(self):
        self.login(self.outsider)
        self.assertEqual(self.client.patch(f'/api/notas/{self.a.pk}/preferencia/', {'fixada': True}, format='json').status_code, 404)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.post('/api/notas/ordenar/', {'projeto': self.project.pk, 'ids': []}, format='json').status_code, 401)
