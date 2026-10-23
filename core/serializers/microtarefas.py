from rest_framework import serializers

from core.models import MicroTarefa, Tarefa


class MicroTarefaSerializer(serializers.ModelSerializer):
    tarefa = serializers.PrimaryKeyRelatedField(queryset=Tarefa.objects.all())

    class Meta:
        model = MicroTarefa
        fields = ['id', 'tarefa', 'titulo', 'descricao', 'ordem', 'concluida', 'data_criacao']
        read_only_fields = ['id', 'data_criacao']

    def validate(self, attrs):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError('Autenticação obrigatória.')

        tarefa = attrs.get('tarefa', getattr(self.instance, 'tarefa', None))
        if tarefa is None:
            raise serializers.ValidationError({'tarefa': 'Tarefa obrigatória.'})
        if not tarefa.projeto.membros.filter(usuario=request.user).exists():
            raise serializers.ValidationError({'tarefa': 'Você não participa deste projeto.'})
        if self.instance and tarefa.pk != self.instance.tarefa_id and self.instance.concluida:
            raise serializers.ValidationError({'tarefa': 'Reabra a etapa antes de movê-la.'})

        ordem = attrs.get('ordem', getattr(self.instance, 'ordem', None))
        if ordem is None or ordem < 1:
            raise serializers.ValidationError({'ordem': 'A ordem deve ser maior que zero.'})

        concluida = attrs.get('concluida', getattr(self.instance, 'concluida', False))
        if not concluida and tarefa.tarefas_dependentes.filter(status=Tarefa.STATUS_CONCLUIDO).exists():
            raise serializers.ValidationError({'concluida': 'Reabra primeiro as tarefas que dependem desta.'})
        outras = list(tarefa.microtarefas.exclude(pk=self.instance.pk if self.instance else None))
        anteriores = [item for item in outras if item.ordem < ordem]
        posteriores = [item for item in outras if item.ordem > ordem]

        if concluida:
            if tarefa.dependencias_pendentes().exists():
                raise serializers.ValidationError({'concluida': 'Conclua as dependências da tarefa primeiro.'})
            if any(not item.concluida for item in anteriores):
                raise serializers.ValidationError({'concluida': 'Conclua todas as etapas anteriores primeiro.'})
        elif any(item.concluida for item in posteriores):
            raise serializers.ValidationError({'concluida': 'Reabra as etapas posteriores primeiro.'})

        if any(item.concluida for item in anteriores) and any(not item.concluida for item in anteriores):
            raise serializers.ValidationError({'ordem': 'A sequência de etapas está inconsistente.'})
        if any(item.concluida for item in posteriores) and not concluida:
            raise serializers.ValidationError({'ordem': 'Não é possível colocar uma etapa pendente antes de uma concluída.'})

        return attrs
