from django.conf import settings
from django.db import models

class ComentarioTarefa(models.Model):
    tarefa = models.ForeignKey('core.Tarefa', on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='comentarios_tarefa')
    conteudo = models.TextField(max_length=5000)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['criado_em', 'id']
