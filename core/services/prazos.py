from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from core.models import Tarefa
from core.models.alerta_prazo import AlertaPrazo
from core.services.notificacoes import criar_notificacao


def prazo_efetivo(tarefa):
    """O prazo antecipado é a meta preferencial; quando ausente, usa-se o oficial."""
    return tarefa.prazo_antecipado or tarefa.data_limite


def dados_prazo(tarefa, hoje=None):
    hoje = hoje or timezone.localdate()
    prazo = prazo_efetivo(tarefa)
    concluida = tarefa.status == Tarefa.STATUS_CONCLUIDO or tarefa.concluida
    dias = (prazo - hoje).days if prazo else None
    return {
        'prazo_efetivo': prazo.isoformat() if prazo else None,
        'dias_para_prazo': dias,
        'atrasada': bool(not concluida and dias is not None and dias < 0),
        'vence_hoje': bool(not concluida and dias == 0),
    }


def processar_alertas_prazo(hoje=None):
    """Executar diariamente via agendador; idempotente mesmo após reexecuções."""
    hoje = hoje or timezone.localdate()
    resumo = {'amanha': 0, 'hoje': 0, 'atrasada': 0}
    tarefas = Tarefa.objects.exclude(status=Tarefa.STATUS_CONCLUIDO).filter(
        concluida=False,
    ).filter(
    ).filter(
        Q(data_limite__isnull=False) | Q(prazo_antecipado__isnull=False),
    ).select_related('projeto', 'responsavel')

    for tarefa in tarefas.iterator():
        prazo = prazo_efetivo(tarefa)
        if not prazo:
            continue
        dias = (prazo - hoje).days
        if dias > 1:
            continue
        if dias == 1:
            tipo, titulo = 'amanha', 'Tarefa vence amanhã'
        elif dias == 0:
            tipo, titulo = 'hoje', 'Tarefa vence hoje'
        else:
            tipo, titulo = 'atrasada', 'Tarefa atrasada'

        # Se houver responsável, avisa apenas ele. Caso contrário, todos os membros.
        if tarefa.responsavel_id:
            user_ids = [tarefa.responsavel_id]
        else:
            user_ids = list(tarefa.projeto.membros.values_list('usuario_id', flat=True).distinct())

        for user_id in set(user_ids):
            # A tarefa pode ter sido concluída enquanto o job estava em execução.
            with transaction.atomic():
                atual = Tarefa.objects.select_for_update().get(pk=tarefa.pk)
                if atual.status == Tarefa.STATUS_CONCLUIDO or atual.concluida:
                    continue
                if prazo_efetivo(atual) != prazo:
                    continue
                registro, novo = AlertaPrazo.objects.get_or_create(
                    tarefa=atual,
                    destinatario_id=user_id,
                    tipo=tipo,
                    prazo=prazo,
                )
                if not novo:
                    continue
                from django.contrib.auth import get_user_model
                usuario = get_user_model().objects.get(pk=user_id)
                criar_notificacao(
                    destinatario=usuario,
                    ator=None,
                    projeto=atual.projeto,
                    tarefa=atual,
                    tipo=f'prazo_{tipo}',
                    titulo=titulo,
                    mensagem=f'A tarefa "{atual.titulo}" do projeto "{atual.projeto.nome}" tem prazo em {prazo:%d/%m/%Y}.',
                    link=f'/projects/{atual.projeto_id}/tasks',
                )
                resumo[tipo] += 1
    return resumo
