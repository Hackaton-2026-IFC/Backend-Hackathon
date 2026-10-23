from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from .projetos import Projeto


class Tarefa(models.Model):
    STATUS_PLANEJADO = 'planejado'
    STATUS_EM_ANDAMENTO = 'em_andamento'
    STATUS_CONCLUIDO = 'concluido'

    PRIORIDADE_MUITO_BAIXA = 'muito_baixa'
    PRIORIDADE_BAIXA = 'baixa'
    PRIORIDADE_NEUTRA = 'neutra'
    PRIORIDADE_ALTA = 'alta'
    PRIORIDADE_MUITO_ALTA = 'muito_alta'

    STATUS_CHOICES = (
        (STATUS_PLANEJADO, 'Planejado'),
        (STATUS_EM_ANDAMENTO, 'Em andamento'),
        (STATUS_CONCLUIDO, 'Concluído'),
    )

    PRIORIDADE_CHOICES = (
        (PRIORIDADE_MUITO_BAIXA, 'Muito baixa'),
        (PRIORIDADE_BAIXA, 'Baixa'),
        (PRIORIDADE_NEUTRA, 'Neutra'),
        (PRIORIDADE_ALTA, 'Alta'),
        (PRIORIDADE_MUITO_ALTA, 'Muito alta'),
    )

    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='tarefas')
    titulo = models.CharField(max_length=150)
    descricao = models.TextField(blank=True, default='')
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default=PRIORIDADE_NEUTRA)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLANEJADO)
    dependencias = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='tarefas_dependentes')
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tarefas_responsavel',
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tarefas_criadas',
    )
    concluida = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_limite = models.DateField(null=True, blank=True)
    prazo_antecipado = models.DateField(null=True, blank=True)
    clima_influencia = models.BooleanField(default=False)
    localizacao = models.CharField(max_length=255, blank=True, default='')
    urgencia_manual = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, null=True, blank=True)

    @property
    def urgencia(self):
        if self.status == self.STATUS_CONCLUIDO or self.concluida:
            return None
        if self.urgencia_manual:
            return self.urgencia_manual
        prazo = self.prazo_antecipado or self.data_limite
        if prazo is None:
            return self.PRIORIDADE_NEUTRA
        dias = (prazo - timezone.localdate()).days
        if dias <= 0:
            return self.PRIORIDADE_MUITO_ALTA
        if dias <= 2:
            return self.PRIORIDADE_ALTA
        if dias <= 7:
            return self.PRIORIDADE_NEUTRA
        if dias <= 14:
            return self.PRIORIDADE_BAIXA
        return self.PRIORIDADE_MUITO_BAIXA

    def dependencias_pendentes(self):
        if not self.pk:
            return Tarefa.objects.none()
        return self.dependencias.exclude(status=self.STATUS_CONCLUIDO)

    def recalcular_status(self):
        microtarefas = list(self.microtarefas.all())
        if microtarefas:
            if all(item.concluida for item in microtarefas) and not self.dependencias_pendentes().exists():
                novo_status = self.STATUS_CONCLUIDO
            elif any(item.concluida for item in microtarefas):
                novo_status = self.STATUS_EM_ANDAMENTO
            else:
                novo_status = self.STATUS_PLANEJADO
        else:
            novo_status = self.status

        if novo_status == self.STATUS_CONCLUIDO and self.dependencias_pendentes().exists():
            novo_status = self.STATUS_PLANEJADO

        self.status = novo_status
        self.concluida = novo_status == self.STATUS_CONCLUIDO
        self.save(update_fields=['status', 'concluida'])

    def __str__(self):
        return self.titulo
