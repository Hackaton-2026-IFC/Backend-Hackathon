from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class Recurso(models.Model):
    TIPO_DOCUMENTO = 'documento'
    TIPO_PASTA = 'pasta'
    TIPO_LINK = 'link'
    TIPO_REPOSITORIO = 'repositorio'
    TIPO_OUTRO = 'outro'
    TIPO_CHOICES = (
        (TIPO_DOCUMENTO, 'Documento'),
        (TIPO_PASTA, 'Pasta'),
        (TIPO_LINK, 'Link'),
        (TIPO_REPOSITORIO, 'Repositório'),
        (TIPO_OUTRO, 'Outro'),
    )

    projeto = models.ForeignKey('core.Projeto', on_delete=models.CASCADE, related_name='recursos')
    tarefa = models.ForeignKey(
        'core.Tarefa', on_delete=models.CASCADE, related_name='recursos',
        null=True, blank=True,
    )
    titulo = models.CharField(max_length=150)
    url = models.URLField(max_length=2000)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_LINK)
    descricao = models.TextField(blank=True, default='')
    adicionado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='recursos_adicionados',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em', '-id']

    def clean(self):
        super().clean()
        if self.tarefa_id and self.projeto_id and self.tarefa.projeto_id != self.projeto_id:
            raise ValidationError({'tarefa': 'A tarefa deve pertencer ao mesmo projeto.'})

    def __str__(self):
        return self.titulo
