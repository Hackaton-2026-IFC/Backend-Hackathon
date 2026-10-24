from rest_framework import serializers

from core.models import Notificacao


class NotificacaoSerializer(serializers.ModelSerializer):
    ator_nome = serializers.CharField(source='ator.name', read_only=True, allow_null=True)
    lida = serializers.SerializerMethodField()

    class Meta:
        model = Notificacao
        fields = [
            'id',
            'tipo',
            'titulo',
            'mensagem',
            'link',
            'projeto',
            'tarefa',
            'ator',
            'ator_nome',
            'lida',
            'lida_em',
            'email_enviado',
            'criada_em',
        ]
        read_only_fields = fields

    def get_lida(self, obj):
        return obj.lida_em is not None
