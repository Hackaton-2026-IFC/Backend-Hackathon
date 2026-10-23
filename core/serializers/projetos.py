from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.models import Projeto, ProjetoMembro

User = get_user_model()


class ProjetoMembroSerializer(serializers.ModelSerializer):
    usuario = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = ProjetoMembro
        fields = ['id', 'usuario', 'cargo']
        read_only_fields = ['id']


class ProjetoSerializer(serializers.ModelSerializer):
    criador = serializers.PrimaryKeyRelatedField(read_only=True)
    criador_hidden = serializers.HiddenField(default=serializers.CurrentUserDefault(), source='criador')
    participantes = serializers.SerializerMethodField()

    class Meta:
        model = Projeto
        fields = ['id', 'nome', 'descricao', 'cor', 'data_criacao', 'criador', 'criador_hidden', 'participantes']
        read_only_fields = ['id', 'data_criacao', 'criador', 'participantes']

    def get_participantes(self, obj):
        return ProjetoMembroSerializer(obj.membros.all(), many=True).data

    def create(self, validated_data):
        projeto = Projeto.objects.create(**validated_data)
        ProjetoMembro.objects.create(projeto=projeto, usuario=projeto.criador, cargo=ProjetoMembro.CARGO_OWNER)
        return projeto
