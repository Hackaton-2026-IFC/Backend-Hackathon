from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()

class DoisPrazosTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='prazos@example.com', password='SenhaForte123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_prazos_do_projeto(self):
        r = self.client.post('/api/projetos/', {'nome': 'Teste', 'data_limite': '2026-11-20', 'prazo_antecipado': '2026-11-15'}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data['prazo_antecipado'], '2026-11-15')
        pid = r.data['id']
        self.assertEqual(self.client.patch(f'/api/projetos/{pid}/', {'prazo_antecipado': '2026-11-25'}, format='json').status_code, 400)
        self.assertEqual(self.client.patch(f'/api/projetos/{pid}/', {'data_limite': '2026-11-10'}, format='json').status_code, 400)
        self.assertEqual(self.client.patch(f'/api/projetos/{pid}/', {'prazo_antecipado': None}, format='json').status_code, 200)

    def test_prazos_da_tarefa(self):
        projeto = self.client.post('/api/projetos/', {'nome': 'P'}, format='json').data['id']
        r = self.client.post('/api/tarefas/', {'projeto': projeto, 'titulo': 'Fazer', 'data_limite': '2026-11-20', 'prazo_antecipado': '2026-11-12'}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        pk = r.data['id']
        self.assertEqual(self.client.patch(f'/api/tarefas/{pk}/', {'prazo_antecipado': '2026-12-01'}, format='json').status_code, 400)
        self.assertEqual(self.client.patch(f'/api/tarefas/{pk}/', {'data_limite': None}, format='json').status_code, 400)

    def test_antecipado_sem_oficial_rejeitado(self):
        r = self.client.post('/api/projetos/', {'nome': 'Sem oficial', 'prazo_antecipado': '2026-11-12'}, format='json')
        self.assertEqual(r.status_code, 400)
