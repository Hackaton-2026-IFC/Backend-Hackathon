import re
from urllib.parse import urlsplit

from PIL import Image as PillowImage

from rest_framework import serializers

from core.models import Nota, NotaPreferencia, Projeto


HEX_COLOR = re.compile(r'^#[0-9A-Fa-f]{6}$')


class NotaSerializer(serializers.ModelSerializer):
    usuario = serializers.PrimaryKeyRelatedField(read_only=True)
    imagem_url = serializers.SerializerMethodField()
    fixada = serializers.BooleanField(required=False)
    ordem = serializers.SerializerMethodField()
    usuario_nome = serializers.CharField(source='usuario.name', read_only=True, allow_null=True)

    class Meta:
        model = Nota
        fields = [
            'id',
            'usuario',
            'usuario_nome',
            'projeto',
            'titulo',
            'conteudo',
            'link',
            'imagem',
            'imagem_url',
            'cor',
            'fixada',
            'ordem',
            'arquivada',
            'etiquetas',
            'lembrete_em',
            'criada_em',
            'atualizada_em',
        ]
        read_only_fields = ['id', 'usuario', 'usuario_nome', 'imagem_url', 'ordem', 'criada_em', 'atualizada_em']
        extra_kwargs = {'imagem': {'write_only': True, 'required': False, 'allow_null': True}}

    def get_ordem(self, obj):
        if hasattr(obj, 'ordem_usuario'):
            return obj.ordem_usuario
        user = self.context.get('request').user if self.context.get('request') else None
        if not user or not user.is_authenticated:
            return None
        return NotaPreferencia.objects.filter(nota=obj, usuario=user).values_list('ordem', flat=True).first()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if hasattr(instance, 'fixada_usuario'):
            data['fixada'] = bool(instance.fixada_usuario)
        else:
            request = self.context.get('request')
            user = request.user if request else None
            data['fixada'] = bool(
                user and user.is_authenticated
                and NotaPreferencia.objects.filter(nota=instance, usuario=user, fixada=True).exists()
            )
        return data

    def create(self, validated_data):
        fixada = validated_data.pop('fixada', False)
        nota = super().create(validated_data)
        if fixada:
            NotaPreferencia.objects.create(nota=nota, usuario=nota.usuario, fixada=True)
        nota.fixada_usuario = fixada
        nota.ordem_usuario = None
        return nota

    def update(self, instance, validated_data):
        # Só o autor pode editar a nota. A ação /preferencia/ permite
        # que qualquer membro fixe/desafixe sem editar a nota de outro autor.
        fixada = validated_data.pop('fixada', None)
        nota = super().update(instance, validated_data)
        if fixada is not None:
            preference, _ = NotaPreferencia.objects.update_or_create(
                nota=nota,
                usuario=self.context['request'].user,
                defaults={'fixada': fixada},
            )
            nota.fixada_usuario = preference.fixada
            nota.ordem_usuario = preference.ordem
        return nota

    def get_imagem_url(self, obj):
        if not obj.imagem:
            return None
        url = obj.imagem.url
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url

    def validate_link(self, value):
        if value and (urlsplit(value).scheme not in ('http', 'https')):
            raise serializers.ValidationError('Use um link HTTP ou HTTPS.')
        return value

    def validate_imagem(self, value):
        if value is None:
            return None
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('A imagem deve ter até 5 MB.')
        try:
            photo = PillowImage.open(value)
            image_format = photo.format
            width, height = photo.size
            photo.verify()
        except (OSError, ValueError, PillowImage.DecompressionBombError) as exc:
            raise serializers.ValidationError('Arquivo de imagem inválido.') from exc
        finally:
            value.seek(0)
        if image_format not in ('JPEG', 'PNG', 'WEBP', 'GIF'):
            raise serializers.ValidationError('Formato permitido: JPG, PNG, WEBP ou GIF.')
        if width * height > 20_000_000:
            raise serializers.ValidationError('A imagem não pode ultrapassar 20 megapixels.')
        return value

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
        link = attrs.get('link', getattr(self.instance, 'link', ''))
        imagem = attrs.get('imagem', getattr(self.instance, 'imagem', None))
        if not titulo.strip() and not conteudo.strip() and not link and not imagem:
            raise serializers.ValidationError('A ideia precisa ter texto, título, link ou imagem.')
        return attrs
