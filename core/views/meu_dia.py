from datetime import date
from django.utils import timezone
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core.models import Tarefa
from core.serializers import TarefaSerializer

WEIGHT = {'muito_baixa': 0, 'baixa': 10, 'neutra': 20, 'alta': 30, 'muito_alta': 40}

def evaluate(task, today):
    reasons = []
    score = WEIGHT.get(task.prioridade, 20)
    if task.prioridade in ('alta', 'muito_alta'):
        reasons.append('Prioridade definida pelo projeto')
    urgency = task.urgencia
    score += WEIGHT.get(urgency, 0)
    if urgency in ('alta', 'muito_alta'):
        reasons.append('Urgência elevada')
    deadline = task.prazo_antecipado or task.data_limite
    if deadline:
        days = (deadline - today).days
        if days < 0:
            score += 70
            reasons.append('Prazo vencido')
        elif days == 0:
            score += 60
            reasons.append('Prazo hoje')
        elif days <= 2:
            score += 40
            reasons.append('Prazo em até dois dias')
        elif days <= 7:
            score += 15
    blocked = any(x.status != Tarefa.STATUS_CONCLUIDO for x in task.dependencias.all())
    if blocked:
        score -= 100
        reasons.append('Bloqueada por dependências pendentes')
    dependent_count = sum(1 for x in task.tarefas_dependentes.all() if x.status != Tarefa.STATUS_CONCLUIDO)
    if not blocked and dependent_count:
        score += min(dependent_count * 12, 48)
        reasons.append('Libera outras tarefas')
    if not reasons:
        reasons.append('Tarefa disponível para execução')
    return score, blocked, reasons

class MeuDiaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Tarefa.objects.filter(projeto__membros__usuario=request.user).exclude(
            status=Tarefa.STATUS_CONCLUIDO).distinct().prefetch_related(
            'dependencias', 'tarefas_dependentes', 'microtarefas')
        # Por padrão, tarefas atribuídas ao usuário ou sem responsável.
        if request.query_params.get('equipe') != 'true':
            qs = qs.filter(Q(responsavel=request.user) | Q(responsavel__isnull=True))
        today = timezone.localdate()
        evaluated = [(task, *evaluate(task, today)) for task in qs]
        evaluated.sort(key=lambda x: (-x[1], x[0].data_limite or date.max, x[0].pk))
        count = min(max(int(request.query_params.get('limite', 10)), 1), 50) if request.query_params.get('limite', '10').isdigit() else 10
        return Response({
            'data': today.isoformat(),
            'total_pendentes': len(evaluated),
            'total_bloqueadas': sum(blocked for _, _, blocked, _ in evaluated),
            'recomendacoes': [{
                'tarefa': TarefaSerializer(task, context={'request': request}).data,
                'pontuacao': score,
                'bloqueada': blocked,
                'motivos': reasons,
            } for task, score, blocked, reasons in evaluated[:count]],
        })
