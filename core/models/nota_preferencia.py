from django.conf import settings
from django.db import models


class NotaPreferencia(models.Model):
    """Posição e fixação são individuais, nunca propriedades globais do mural."""

    nota = models.ForeignKey('core.Nota', on_delete=models.CASCADE, related_name='preferencias')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferencias_notas')
    fixada = models.BooleanField(default=False)
    ordem = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['nota', 'usuario'], name='nota_preferencia_por_usuario_unica'),
        ]
