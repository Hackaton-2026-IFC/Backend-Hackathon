from django.core.exceptions import ValidationError
from django.db import models, transaction

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
        antiga_tarefa_id = None
        if self.pk:
            antiga_tarefa_id = type(self).objects.filter(pk=self.pk).values_list('tarefa_id', flat=True).first()
        with transaction.atomic():
            super().save(*args, **kwargs)
            self.tarefa.recalcular_status()
            if antiga_tarefa_id and antiga_tarefa_id != self.tarefa_id:
                Tarefa.objects.get(pk=antiga_tarefa_id).recalcular_status()

    def delete(self, *args, **kwargs):
        tarefa = self.tarefa
        with transaction.atomic():
            resultado = super().delete(*args, **kwargs)
            tarefa.recalcular_status()
            return resultado

    def __str__(self):
        return f'{self.tarefa} - {self.titulo}'
