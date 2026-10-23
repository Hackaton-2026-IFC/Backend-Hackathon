from rest_framework import serializers

from core.models import Projeto, Tarefa


class TarefaSerializer(serializers.ModelSerializer):
    projeto = serializers.PrimaryKeyRelatedField(queryset=Projeto.objects.all())
    criado_por = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Tarefa
        fields = [
            'id',
            'projeto',
            'titulo',
            'descricao',
            'prioridade',
            'responsavel',
            'criado_por',
            'concluida',
            'data_criacao',
            'data_limite',
        ]
        read_only_fields = ['id', 'data_criacao', 'criado_por']
