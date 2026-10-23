import os
import requests
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from core.models.google_identity import GoogleIdentity

User = get_user_model()

class GoogleCredentialSerializer(serializers.Serializer):
    credential = serializers.CharField(trim_whitespace=False)

def validated_google_identity(credential):
    audience = os.environ.get('GOOGLE_CLIENT_ID')
    if not audience:
        raise serializers.ValidationError({'detail': 'GOOGLE_CLIENT_ID não configurado no servidor.'})
    try:
        response = requests.get('https://oauth2.googleapis.com/tokeninfo',
                                params={'id_token': credential}, timeout=7)
        if response.status_code != 200:
            raise serializers.ValidationError({'credential': 'Credencial Google inválida ou expirada.'})
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise serializers.ValidationError({'credential': 'Falha ao validar credencial Google.'}) from exc
    if payload.get('aud') != audience or payload.get('iss') not in ('accounts.google.com', 'https://accounts.google.com'):
        raise serializers.ValidationError({'credential': 'Identidade Google não autorizada para esta aplicação.'})
    if payload.get('email_verified') not in (True, 'true'):
        raise serializers.ValidationError({'credential': 'Conta Google sem e-mail verificado.'})
    if not payload.get('sub') or not payload.get('email'):
        raise serializers.ValidationError({'credential': 'Identidade Google incompleta.'})
    return payload

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'google_auth'

    def post(self, request):
        serializer = GoogleCredentialSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = validated_google_identity(serializer.validated_data['credential'])
        sub, email = payload['sub'], payload['email']
        identity = GoogleIdentity.objects.select_related('user').filter(sub=sub).first()
        if identity:
            user = identity.user
        else:
            if User.objects.filter(email__iexact=email).exists():
                return Response({'detail': 'Este e-mail já possui uma conta. Entre com a senha e vincule o Google no perfil.'}, status=409)
            try:
                with transaction.atomic():
                    user = User.objects.create_user(email=email, name=payload.get('name', ''))
                    user.set_unusable_password()
                    user.save(update_fields=['password'])
                    GoogleIdentity.objects.create(user=user, sub=sub)
            except IntegrityError:
                return Response({'detail': 'A conta foi alterada durante o cadastro. Tente novamente.'}, status=409)
        if not user.is_active:
            return Response({'detail': 'Conta desativada.'}, status=403)
        refresh = RefreshToken.for_user(user)
        refresh['auth_provider'] = 'google'
        return Response({'access': str(refresh.access_token), 'refresh': str(refresh),
                         'user_id': user.pk}, status=status.HTTP_200_OK)

class GoogleLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GoogleCredentialSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = validated_google_identity(serializer.validated_data['credential'])
        if payload['email'].casefold() != request.user.email.casefold():
            return Response({'detail': 'A conta Google deve possuir o mesmo e-mail desta conta.'}, status=400)
        if GoogleIdentity.objects.filter(sub=payload['sub']).exclude(user=request.user).exists():
            return Response({'detail': 'Conta Google já vinculada a outro usuário.'}, status=409)
        if GoogleIdentity.objects.filter(user=request.user).exclude(sub=payload['sub']).exists():
            return Response({'detail': 'Esta conta já tem outro Google vinculado.'}, status=409)
        try:
            GoogleIdentity.objects.get_or_create(user=request.user, defaults={'sub': payload['sub']})
        except IntegrityError:
            return Response({'detail': 'Conflito ao vincular identidade Google.'}, status=409)
        return Response({'google_vinculado': True})

    def get(self, request):
        return Response({'google_vinculado': GoogleIdentity.objects.filter(user=request.user).exists()})
