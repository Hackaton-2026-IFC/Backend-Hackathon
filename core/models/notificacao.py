from django.conf import settings
from django.db import models


class Notificacao(models.Model):
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificacoes',
    )
    ator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notificacoes_geradas',
    )
    projeto = models.ForeignKey(
        'core.Projeto',
        on_delete=models.CASCADE,
        related_name='notificacoes',
    )
    tarefa = models.ForeignKey(
        'core.Tarefa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notificacoes',
    )
    tipo = models.CharField(max_length=40)
    titulo = models.CharField(max_length=180)
    mensagem = models.TextField(blank=True, default='')
    link = models.CharField(max_length=300, blank=True, default='')
    lida_em = models.DateTimeField(null=True, blank=True)
    email_enviado = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criada_em', '-id']
        indexes = [
            models.Index(
                fields=['destinatario', 'lida_em', 'criada_em'],
                name='core_notifi_destina_67c95d_idx',
            ),
        ]

    def __str__(self):
        return f'{self.destinatario_id}: {self.titulo}'
