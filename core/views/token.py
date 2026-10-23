from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
    TokenVerifySerializer,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        **TokenObtainPairSerializer.default_error_messages,
        'no_active_account': 'Não foi encontrada uma conta ativa com as credenciais informadas.',
    }


@extend_schema_view(
    post=extend_schema(
        summary="Obter token JWT",
        description="Autentica com e-mail e senha. Retorna access token e refresh token.",
        request=CustomTokenObtainPairSerializer,
        responses={200: TokenObtainPairSerializer, 401: None},
    )
)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'


@extend_schema_view(
    post=extend_schema(
        summary="Atualizar token JWT",
        description="Retorna um novo access token a partir do refresh token.",
        request=TokenRefreshSerializer,
        responses={200: TokenRefreshSerializer, 401: None},
    )
)
class CustomTokenRefreshView(TokenRefreshView):
    pass


@extend_schema_view(
    post=extend_schema(
        summary="Verificar token JWT",
        description="Verifica se um token JWT (access ou refresh) é válido.",
        request=TokenVerifySerializer,
        responses={200: None, 401: None},
    )
)
class CustomTokenVerifyView(TokenVerifyView):
    pass
