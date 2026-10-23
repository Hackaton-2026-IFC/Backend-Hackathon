from django.conf import settings
from django.db import models

from .projetos import Projeto


class Tarefa(models.Model):
    PRIORIDADE_MUITO_BAIXA = 'muito_baixa'
    PRIORIDADE_BAIXA = 'baixa'
    PRIORIDADE_NEUTRA = 'neutra'
    PRIORIDADE_ALTA = 'alta'
    PRIORIDADE_MUITO_ALTA = 'muito_alta'

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

    def __str__(self):
        return self.titulo
