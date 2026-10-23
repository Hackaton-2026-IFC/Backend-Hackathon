from datetime import date, datetime
from decimal import Decimal
from core.models.atividade import Atividade

FIELDS = ('titulo', 'descricao', 'status', 'prioridade', 'responsavel_id',
          'data_limite', 'prazo_antecipado', 'urgencia_manual',
          'concluida', 'clima_influencia', 'localizacao', 'projeto_id')

def snapshot(task):
    data = {field: getattr(task, field) for field in FIELDS}
    data['dependencias'] = sorted(task.dependencias.values_list('id', flat=True))
    return data

def to_json(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value

def registrar(task, autor, acao, antes=None, depois=None):
    changes = {}
    if antes is not None and depois is not None:
        changes = {
            name: {'antes': to_json(antes.get(name)), 'depois': to_json(depois.get(name))}
            for name in (antes.keys() | depois.keys())
            if antes.get(name) != depois.get(name)
        }
        if not changes:
            return None
    return Atividade.objects.create(
        projeto=task.projeto, tarefa=task if task.pk else None,
        tarefa_id_original=task.pk, tarefa_titulo=task.titulo, autor=autor,
        acao=acao, alteracoes=changes,
    )
