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

        ordem = attrs.get('ordem', getattr(self.instance, 'ordem', None))
        if ordem is None:
            raise serializers.ValidationError({'ordem': 'A ordem da microtarefa é obrigatória.'})

        if attrs.get('concluida', getattr(self.instance, 'concluida', False)):
            microtarefas_anteriores = tarefa.microtarefas.filter(ordem__lt=ordem)
            if microtarefas_anteriores.exclude(concluida=True).exists():
                raise serializers.ValidationError({
                    'concluida': 'Para concluir esta microtarefa, as anteriores precisam estar concluídas.'
                })

        return attrs
