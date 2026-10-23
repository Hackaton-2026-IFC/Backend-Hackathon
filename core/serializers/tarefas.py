from rest_framework import serializers

from core.models import Projeto, Tarefa


class TarefaSerializer(serializers.ModelSerializer):
    projeto = serializers.PrimaryKeyRelatedField(queryset=Projeto.objects.all())
    criado_por = serializers.PrimaryKeyRelatedField(read_only=True)

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

    def validate(self, attrs):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError('Autenticação obrigatória.')

        projeto = attrs.get('projeto', self.instance.projeto if self.instance else None)
        if projeto is None or not projeto.membros.filter(usuario=request.user).exists():
            raise serializers.ValidationError({'projeto': 'Você não participa deste projeto.'})

        responsavel = attrs.get('responsavel', self.instance.responsavel if self.instance else None)
        if responsavel is not None and not projeto.membros.filter(usuario=responsavel).exists():
            raise serializers.ValidationError({'responsavel': 'O responsável deve participar do projeto.'})
        return attrs
