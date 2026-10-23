import re

from rest_framework import serializers

from core.models import Nota, Projeto


HEX_COLOR = re.compile(r'^#[0-9A-Fa-f]{6}$')


class NotaSerializer(serializers.ModelSerializer):
    usuario = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Nota
        fields = [
            'id',
            'usuario',
            'projeto',
            'titulo',
            'conteudo',
            'cor',
            'fixada',
            'arquivada',
            'etiquetas',
            'lembrete_em',
            'criada_em',
            'atualizada_em',
        ]
        read_only_fields = ['id', 'usuario', 'criada_em', 'atualizada_em']

    def validate_cor(self, value):
        if not HEX_COLOR.fullmatch(value):
            raise serializers.ValidationError('Use uma cor hexadecimal no formato #RRGGBB.')
        return value.upper()

    def validate_etiquetas(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Etiquetas devem ser uma lista.')
        cleaned = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise serializers.ValidationError('Cada etiqueta deve ser um texto não vazio.')
            label = item.strip()
            if len(label) > 30:
                raise serializers.ValidationError('Cada etiqueta pode ter no máximo 30 caracteres.')
            if label not in cleaned:
                cleaned.append(label)
        if len(cleaned) > 20:
            raise serializers.ValidationError('Uma nota pode ter no máximo 20 etiquetas.')
        return cleaned

    def validate_projeto(self, projeto):
        request = self.context.get('request')
        if request and projeto and not projeto.membros.filter(usuario=request.user).exists():
            raise serializers.ValidationError('Você não participa deste projeto.')
        return projeto

    def validate(self, attrs):
        titulo = attrs.get('titulo', getattr(self.instance, 'titulo', ''))
        conteudo = attrs.get('conteudo', getattr(self.instance, 'conteudo', ''))
        if not titulo.strip() and not conteudo.strip():
            raise serializers.ValidationError('A nota precisa ter título ou conteúdo.')
        return attrs
