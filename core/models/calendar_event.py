from django.conf import settings
from django.db import models

class CalendarEvent(models.Model):
    projeto = models.ForeignKey('core.Projeto', on_delete=models.CASCADE, related_name='eventos')
    titulo = models.CharField(max_length=150)
    descricao = models.TextField(blank=True, default='')
    data = models.DateField()
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fim = models.TimeField(null=True, blank=True)
    localizacao = models.CharField(max_length=255, blank=True, default='')
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    class Meta:
        ordering = ['data', 'hora_inicio', 'id']
