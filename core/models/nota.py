from django.conf import settings
from django.db import models


class Nota(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notas',
    )
    projeto = models.ForeignKey(
        'core.Projeto',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notas',
    )
    titulo = models.CharField(max_length=200, blank=True, default='')
    conteudo = models.TextField(blank=True, default='')
    link = models.URLField(max_length=2000, blank=True, default='')
    imagem = models.ImageField(upload_to='notas/imagens/%Y/%m/', blank=True, null=True)
    cor = models.CharField(max_length=7, default='#FFF475')
    fixada = models.BooleanField(default=False)
    arquivada = models.BooleanField(default=False)
    etiquetas = models.JSONField(default=list, blank=True)
    lembrete_em = models.DateTimeField(null=True, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fixada', '-atualizada_em', '-id']
        indexes = [
            models.Index(fields=['usuario', 'arquivada', 'fixada'], name='core_nota_usuario_012f10_idx'),
            models.Index(fields=['usuario', 'projeto'], name='core_nota_usuario_38f65d_idx'),
        ]

    def __str__(self):
        return self.titulo or f'Nota #{self.pk}'
