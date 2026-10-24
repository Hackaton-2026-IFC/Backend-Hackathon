from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from core.models import AlertaPrazo, Notificacao, ProjetoMembro, Tarefa
from core.services.prazos import dados_prazo, processar_alertas_prazo


User = get_user_model()


class DeadlineAlertTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='deadline-owner@test.com', password='12345678')
        self.member = User.objects.create_user(email='deadline-member@test.com', password='12345678')
        from core.models import Projeto
        self.project = Projeto.objects.create(nome='Prazos', criador=self.owner)
        ProjetoMembro.objects.create(projeto=self.project, usuario=self.owner, cargo=ProjetoMembro.CARGO_OWNER)
        ProjetoMembro.objects.create(projeto=self.project, usuario=self.member, cargo=ProjetoMembro.CARGO_MEMBER)
        self.today = timezone.localdate()

    def make_task(self, days, **kwargs):
        return Tarefa.objects.create(
            projeto=self.project,
            titulo='Entrega importante',
            data_limite=self.today + timedelta(days=days),
            **kwargs,
        )

    def test_amanha_hoje_atrasada_e_idempotencia(self):
        for days in (1, 0, -2):
            self.make_task(days, responsavel=self.member)
        with self.captureOnCommitCallbacks(execute=True):
            result = processar_alertas_prazo(self.today)
            again = processar_alertas_prazo(self.today)
        self.assertEqual(result, {'amanha': 1, 'hoje': 1, 'atrasada': 1})
        self.assertEqual(again, {'amanha': 0, 'hoje': 0, 'atrasada': 0})
        self.assertEqual(AlertaPrazo.objects.count(), 3)
        self.assertEqual(Notificacao.objects.count(), 3)
        self.assertFalse(Notificacao.objects.exclude(destinatario=self.member).exists())

    def test_sem_responsavel_avisa_membros_uma_vez(self):
        task = self.make_task(0)
        result = processar_alertas_prazo(self.today)
        self.assertEqual(result['hoje'], 2)
        self.assertEqual(
            set(Notificacao.objects.filter(tarefa=task).values_list('destinatario_id', flat=True)),
            {self.owner.id, self.member.id},
        )
        self.assertEqual(processar_alertas_prazo(self.today)['hoje'], 0)

    def test_conclusao_para_alertas(self):
        task = self.make_task(1, responsavel=self.member)
        processar_alertas_prazo(self.today)
        task.status = Tarefa.STATUS_CONCLUIDO
        task.concluida = True
        task.save(update_fields=['status', 'concluida'])
        processar_alertas_prazo(self.today + timedelta(days=2))
        self.assertEqual(Notificacao.objects.filter(tarefa=task).count(), 1)

    def test_antecipado_tem_precedencia_e_destaque(self):
        task = Tarefa.objects.create(
            projeto=self.project,
            titulo='Meta antecipada',
            data_limite=self.today + timedelta(days=8),
            prazo_antecipado=self.today - timedelta(days=1),
            responsavel=self.member,
        )
        info = dados_prazo(task, self.today)
        self.assertTrue(info['atrasada'])
        self.assertEqual(info['dias_para_prazo'], -1)
        self.assertEqual(processar_alertas_prazo(self.today)['atrasada'], 1)
        self.assertEqual(Notificacao.objects.get(tarefa=task).tipo, 'prazo_atrasada')

    def test_prazo_editado_gera_novo_alerta_sem_duplicar_antigo(self):
        task = self.make_task(1, responsavel=self.member)
        processar_alertas_prazo(self.today)
        task.data_limite = self.today
        task.save(update_fields=['data_limite'])
        self.assertEqual(processar_alertas_prazo(self.today)['hoje'], 1)
        self.assertEqual(processar_alertas_prazo(self.today)['hoje'], 0)
        self.assertEqual(AlertaPrazo.objects.filter(tarefa=task).count(), 2)

    def test_management_command(self):
        self.make_task(0, responsavel=self.member)
        output = StringIO()
        call_command('processar_prazos', data=self.today.isoformat(), stdout=output)
        self.assertIn('Alertas gerados', output.getvalue())

    def test_alerta_com_apenas_prazo_antecipado(self):
        task = Tarefa.objects.create(
            projeto=self.project, titulo='Meta sem prazo oficial',
            prazo_antecipado=self.today, responsavel=self.member,
        )
        self.assertEqual(processar_alertas_prazo(self.today)['hoje'], 1)
        self.assertEqual(processar_alertas_prazo(self.today)['hoje'], 0)
        self.assertEqual(AlertaPrazo.objects.filter(tarefa=task).count(), 1)
