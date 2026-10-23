from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import MicroTarefa, Projeto, ProjetoMembro, Tarefa
from core.serializers.microtarefas import MicroTarefaSerializer
from core.serializers.tarefas import TarefaSerializer


class DependenciasTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='teste_dep', password='senha_forte_123'
        )
        self.projeto = Projeto.objects.create(nome='Projeto teste', criador=self.user)
        ProjetoMembro.objects.create(projeto=self.projeto, usuario=self.user)
        self.request_context = {'request': SimpleNamespace(user=self.user)}

    def tarefa(self, titulo):
        return Tarefa.objects.create(projeto=self.projeto, titulo=titulo, criado_por=self.user)

    def test_nao_conclui_sem_predecessora(self):
        primeira = self.tarefa('Primeira')
        segunda = self.tarefa('Segunda')
        segunda.dependencias.add(primeira)
        serializer = TarefaSerializer(
            segunda, data={'status': 'concluido'}, partial=True, context=self.request_context
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('dependencias', serializer.errors)

    def test_conclui_apos_predecessora(self):
        primeira = self.tarefa('Primeira')
        segunda = self.tarefa('Segunda')
        segunda.dependencias.add(primeira)
        primeira.status = Tarefa.STATUS_CONCLUIDO
        primeira.concluida = True
        primeira.save(update_fields=['status', 'concluida'])
        serializer = TarefaSerializer(
            segunda, data={'status': 'concluido'}, partial=True, context=self.request_context
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        segunda.refresh_from_db()
        self.assertTrue(segunda.concluida)

    def test_dependencia_circular(self):
        a = self.tarefa('A')
        b = self.tarefa('B')
        a.dependencias.add(b)
        serializer = TarefaSerializer(
            b, data={'dependencias': [a.pk]}, partial=True, context=self.request_context
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('dependencias', serializer.errors)

    def test_microtarefas_em_ordem(self):
        tarefa = self.tarefa('Tarefa')
        primeira = MicroTarefa.objects.create(tarefa=tarefa, titulo='Etapa 1', ordem=1)
        segunda = MicroTarefa.objects.create(tarefa=tarefa, titulo='Etapa 2', ordem=2)
        serializer = MicroTarefaSerializer(
            segunda, data={'concluida': True}, partial=True, context=self.request_context
        )
        self.assertFalse(serializer.is_valid())
        primeira.concluida = True
        primeira.save()
        serializer = MicroTarefaSerializer(
            segunda, data={'concluida': True}, partial=True, context=self.request_context
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        tarefa.refresh_from_db()
        self.assertEqual(tarefa.status, Tarefa.STATUS_CONCLUIDO)

    def test_remocao_recalcula_status(self):
        tarefa = self.tarefa('Tarefa')
        primeira = MicroTarefa.objects.create(tarefa=tarefa, titulo='Primeira', ordem=1, concluida=True)
        segunda = MicroTarefa.objects.create(tarefa=tarefa, titulo='Segunda', ordem=2)
        tarefa.refresh_from_db()
        self.assertEqual(tarefa.status, Tarefa.STATUS_EM_ANDAMENTO)
        segunda.delete()
        tarefa.refresh_from_db()
        self.assertEqual(tarefa.status, Tarefa.STATUS_CONCLUIDO)
