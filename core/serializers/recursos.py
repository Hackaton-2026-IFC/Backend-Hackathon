from urllib.parse import urlsplit

from rest_framework import serializers
from core.models import Recurso


class RecursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recurso
        fields = [
            'id', 'titulo', 'url', 'tipo', 'descricao', 'projeto',
            'tarefa', 'adicionado_por', 'criado_em',
        ]
        read_only_fields = ['id', 'projeto', 'tarefa', 'adicionado_por', 'criado_em']

    def validate_url(self, value):
        if urlsplit(value).scheme.lower() not in ('http', 'https'):
            raise serializers.ValidationError('Use um link HTTP ou HTTPS.')
        return value
