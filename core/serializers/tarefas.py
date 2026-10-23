from rest_framework import serializers

from core.models import Projeto, Tarefa
from core.serializers.microtarefas import MicroTarefaSerializer


class TarefaSerializer(serializers.ModelSerializer):
    projeto = serializers.PrimaryKeyRelatedField(queryset=Projeto.objects.all())
    criado_por = serializers.PrimaryKeyRelatedField(read_only=True)
    microtarefas = MicroTarefaSerializer(many=True, read_only=True)
    status = serializers.ChoiceField(choices=Tarefa.STATUS_CHOICES, required=False)

    class Meta:
        model = Tarefa
        fields = [
            'id',
            'projeto',
            'titulo',
            'descricao',
            'prioridade',
            'status',
            'responsavel',
            'criado_por',
            'concluida',
            'data_criacao',
            'data_limite',
            'microtarefas',
        ]
        read_only_fields = ['id', 'data_criacao', 'criado_por', 'microtarefas']

    def validate(self, attrs):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError('Autenticação obrigatória.')

        projeto = attrs.get('projeto', getattr(self.instance, 'projeto', None))
        if projeto is None or not projeto.membros.filter(usuario=request.user).exists():
            raise serializers.ValidationError({'projeto': 'Você não participa deste projeto.'})

        responsavel = attrs.get('responsavel', getattr(self.instance, 'responsavel', None))
        if responsavel is not None and not projeto.membros.filter(usuario=responsavel).exists():
            raise serializers.ValidationError({'responsavel': 'O responsável deve participar do projeto.'})

        status_desejado = attrs.get('status', getattr(self.instance, 'status', Tarefa.STATUS_PLANEJADO))
        microtarefas = self.instance.microtarefas.all() if self.instance else projeto.tarefas.none()
        if (
            status_desejado == Tarefa.STATUS_CONCLUIDO
            and microtarefas.exists()
            and not all(microtarefa.concluida for microtarefa in microtarefas)
        ):
            raise serializers.ValidationError({
                'status': 'Para concluir a tarefa, todas as microtarefas precisam estar concluídas.'
            })

        return attrs

    def update(self, instance, validated_data):
        if 'status' in validated_data:
            validated_data['concluida'] = validated_data['status'] == Tarefa.STATUS_CONCLUIDO
        return super().update(instance, validated_data)
