from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.models import ConviteProjeto, Projeto, ProjetoMembro

User = get_user_model()


class ConviteProjetoSerializer(serializers.ModelSerializer):
    projeto = serializers.PrimaryKeyRelatedField(queryset=Projeto.objects.all())
    usuario = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    enviado_por = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ConviteProjeto
        fields = ['id', 'projeto', 'usuario', 'enviado_por', 'cargo', 'status', 'criado_em', 'respondido_em']
        read_only_fields = ['id', 'enviado_por', 'status', 'criado_em', 'respondido_em']


    def validate_cargo(self, value):
        # Convites não podem conceder direitos de proprietário.
        if value not in (ProjetoMembro.CARGO_ADMIN, ProjetoMembro.CARGO_MEMBER):
            raise serializers.ValidationError('Só é permitido convidar administradores ou membros.')
        return value


class RespostaConviteSerializer(serializers.ModelSerializer):
    acao = serializers.ChoiceField(choices=['aceitar', 'recusar'])

    class Meta:
        model = ConviteProjeto
        fields = ['acao']
