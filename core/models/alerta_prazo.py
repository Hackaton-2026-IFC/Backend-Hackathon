from django.conf import settings
from django.db import models


class AlertaPrazo(models.Model):
    """Registro único para impedir repetição de avisos entre execuções."""
    tarefa = models.ForeignKey('core.Tarefa', on_delete=models.CASCADE, related_name='alertas_prazo')
    destinatario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=24)
    prazo = models.DateField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tarefa', 'destinatario', 'tipo', 'prazo'],
                name='unique_alerta_prazo_tarefa_usuario_tipo_data',
            )
        ]
