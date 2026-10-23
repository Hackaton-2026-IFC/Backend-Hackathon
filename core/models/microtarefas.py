from django.db import models

from .tarefas import Tarefa


class MicroTarefa(models.Model):
    tarefa = models.ForeignKey(Tarefa, on_delete=models.CASCADE, related_name='microtarefas')
    titulo = models.CharField(max_length=150)
    descricao = models.TextField(blank=True, default='')
    ordem = models.PositiveIntegerField(default=1)
    concluida = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordem', 'id']
        unique_together = ('tarefa', 'ordem')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.tarefa.recalcular_status()

    def __str__(self):
        return f'{self.tarefa} - {self.titulo}'
