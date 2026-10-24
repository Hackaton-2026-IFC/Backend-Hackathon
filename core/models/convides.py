from django.conf import settings
from django.db import models

from .projetos import Projeto, ProjetoMembro


class ConviteProjeto(models.Model):
    STATUS_PENDENTE = 'pendente'
    STATUS_ACEITO = 'aceito'
    STATUS_RECUSADO = 'recusado'

    STATUS_CHOICES = (
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_ACEITO, 'Aceito'),
        (STATUS_RECUSADO, 'Recusado'),
    )

    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='convites')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='convites_projeto')
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='convites_enviados',
    )
    cargo = models.CharField(max_length=20, choices=ProjetoMembro.CARGO_CHOICES, default=ProjetoMembro.CARGO_ADMIN)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    criado_em = models.DateTimeField(auto_now_add=True)
    respondido_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['projeto', 'usuario'],
                condition=models.Q(status='pendente'),
                name='unique_convite_pendente_por_projeto',
            ),
        ]

    def __str__(self):
        return f'{self.usuario} -> {self.projeto} ({self.status})'
