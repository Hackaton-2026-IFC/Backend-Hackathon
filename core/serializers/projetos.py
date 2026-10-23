from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from core.models import Projeto, ProjetoMembro
from uploader.serializers import ImageSerializer

User = get_user_model()


class PerfilPublicoSerializer(serializers.ModelSerializer):
    """Dados seguros do perfil para exibição dos participantes do projeto."""
    profile_image = ImageSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'name', 'username', 'profile_image']
        read_only_fields = fields


class ProjetoMembroSerializer(serializers.ModelSerializer):
    usuario_detalhes = PerfilPublicoSerializer(source='usuario', read_only=True)
    usuario = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = ProjetoMembro
        fields = ['id', 'usuario', 'usuario_detalhes', 'cargo']
        read_only_fields = ['id']


class ProjetoSerializer(serializers.ModelSerializer):
    criador = serializers.PrimaryKeyRelatedField(read_only=True)
    criador_detalhes = PerfilPublicoSerializer(source='criador', read_only=True)
    icone = serializers.ChoiceField(choices=Projeto.ICON_CHOICES, required=False, allow_blank=True)
    participantes = serializers.SerializerMethodField()
    fixado = serializers.SerializerMethodField()

    class Meta:
        model = Projeto
        fields = [
            'id',
            'nome',
            'descricao',
            'cor',
            'icone',
            'status',
            'data_limite',
            'prazo_antecipado',
            'data_criacao',
            'criador',
            'criador_detalhes',
            'participantes',
            'fixado',
        ]
        read_only_fields = ['id', 'data_criacao', 'criador', 'participantes']

    def validate(self, attrs):
        oficial = attrs.get('data_limite', getattr(self.instance, 'data_limite', None))
        antecipado = attrs.get('prazo_antecipado', getattr(self.instance, 'prazo_antecipado', None))
        if antecipado and not oficial:
            raise serializers.ValidationError({'prazo_antecipado': 'Informe o prazo oficial antes do antecipado.'})
        if antecipado and antecipado > oficial:
            raise serializers.ValidationError({'prazo_antecipado': 'O prazo antecipado não pode ultrapassar o oficial.'})
        return attrs

    def get_fixado(self, obj):
        if hasattr(obj, 'fixado_usuario'):
            return obj.fixado_usuario
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated and obj.fixacoes.filter(usuario=request.user).exists())

    def get_participantes(self, obj):
        return ProjetoMembroSerializer(obj.membros.select_related('usuario__profile_image').all(), many=True).data

    @transaction.atomic
    def create(self, validated_data):
        projeto = Projeto.objects.create(**validated_data)
        ProjetoMembro.objects.create(projeto=projeto, usuario=projeto.criador, cargo=ProjetoMembro.CARGO_OWNER)
        return projeto
