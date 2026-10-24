from django.conf import settings
from django.db import models


class GoogleCalendarExport(models.Model):
    """Confirmação da exportação de um evento para a agenda de um usuário."""
    evento = models.ForeignKey('core.CalendarEvent', on_delete=models.CASCADE, related_name='exportacoes_google')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exportacoes_google_agenda')
    google_event_id = models.CharField(max_length=255)
    google_event_url = models.URLField(max_length=2000, blank=True, default='')
    exportado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['evento', 'usuario'], name='google_agenda_evento_usuario_unico'),
        ]
