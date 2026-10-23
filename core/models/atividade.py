from django.conf import settings
from django.db import models

class Atividade(models.Model):
    projeto = models.ForeignKey('core.Projeto', on_delete=models.CASCADE, related_name='atividades')
    tarefa = models.ForeignKey('core.Tarefa', on_delete=models.SET_NULL, null=True, blank=True, related_name='atividades')
    tarefa_id_original = models.BigIntegerField(null=True, blank=True, db_index=True)
    tarefa_titulo = models.CharField(max_length=150, blank=True, default='')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='atividades')
    acao = models.CharField(max_length=40)
    alteracoes = models.JSONField(default=dict, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em', '-id']
