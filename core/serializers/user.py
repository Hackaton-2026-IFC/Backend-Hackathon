from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, SlugRelatedField

from core.models import User
from uploader.models import Image
from uploader.serializers import ImageSerializer


class UserSerializer(ModelSerializer):
    profile_image_attachment_key = SlugRelatedField(
        source='profile_image',
        queryset=Image.objects.all(),
        slug_field='attachment_key',
        required=False,
        allow_null=True,
        write_only=True,
    )
    profile_image = ImageSerializer(required=False, read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'name',
            'username',
            'profile_image',
            'profile_image_attachment_key',
            'is_active',
            'is_staff',
            'is_superuser',
            'last_login',
            'groups',
        ]
        read_only_fields = ['id', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'groups']
        depth = 1


class UserRegistrationSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'username', 'password', 'profile_image']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserDirectorySerializer(ModelSerializer):
    """Dados mínimos para selecionar participantes em projetos."""

    class Meta:
        model = User
        fields = ['id', 'name', 'username']
