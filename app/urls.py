from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

from core.views import (
    CategoriaViewSet,
    ConviteProjetoViewSet,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    MicroTarefaViewSet,
    ProjetoViewSet,
    RecursoViewSet,
    TarefaViewSet,
    UserRegistrationView,
    UserViewSet,
)
from uploader.router import router as uploader_router
from core.views.atividade import ProjectActivityView, TaskActivityView
from core.views.calendario import calendario, calendario_evento, export_google_agenda
from core.views.google_auth import GoogleLoginView, GoogleLinkView
from core.views.meu_dia import MeuDiaView

router = DefaultRouter()

router.register(r'categorias', CategoriaViewSet, basename='categorias')
router.register(r'usuarios', UserViewSet, basename='usuarios')
router.register(r'projetos', ProjetoViewSet, basename='projetos')
router.register(r'tarefas', TarefaViewSet, basename='tarefas')
router.register(r'microtarefas', MicroTarefaViewSet, basename='microtarefas')
router.register(r'convites', ConviteProjetoViewSet, basename='convites')
router.register(r'recursos', RecursoViewSet, basename='recursos')

urlpatterns = [
    path('admin/', admin.site.urls),
    # OpenAPI 3
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/doc/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc',
    ),
    # Autenticação JWT
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', CustomTokenVerifyView.as_view(), name='token_verify'),
    path('api/meu-dia/', MeuDiaView.as_view(), name='meu-dia'),
    path('api/auth/google/', GoogleLoginView.as_view(), name='google-login'),
    path('api/auth/google/vincular/', GoogleLinkView.as_view(), name='google-link'),
    # Registro de usuários
    path('api/registro/', UserRegistrationView.as_view(), name='user_registration'),
    path('api/projetos/<int:pk>/calendario/', calendario, name='calendario-projeto'),
    path('api/projetos/<int:pk>/calendario/<int:event_id>/', calendario_evento, name='calendario-evento'),
    path('api/projetos/<int:pk>/google-agenda/', export_google_agenda, name='google-agenda'),
    path('api/projetos/<int:pk>/atividades/', ProjectActivityView.as_view()),
    path('api/tarefas/<int:pk>/atividades/', TaskActivityView.as_view()),
    # API
    path('api/', include(router.urls)),
    path('api/media/', include(uploader_router.urls)),  # nova linha
]
urlpatterns += static(settings.MEDIA_ENDPOINT, document_root=settings.MEDIA_ROOT)
