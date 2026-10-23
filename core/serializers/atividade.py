from rest_framework import serializers
from core.models.atividade import Atividade

class AtividadeSerializer(serializers.ModelSerializer):
    autor_nome = serializers.CharField(source='autor.name', read_only=True, allow_null=True)
    class Meta:
        model = Atividade
        fields = ('id','projeto','tarefa','tarefa_id_original','tarefa_titulo','autor',
                  'autor_nome','acao','alteracoes','criado_em')
        read_only_fields = fields
