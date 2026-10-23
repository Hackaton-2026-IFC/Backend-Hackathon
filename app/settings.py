import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

import dj_database_url
from dotenv import load_dotenv

# ============================================================
# Carregamento das variáveis de ambiente
# ============================================================

load_dotenv()

# ============================================================
# Caminhos do projeto
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# Configurações básicas
# ============================================================

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
if not DEBUG and SECRET_KEY in ('', 'django-insecure'):
    raise ImproperlyConfigured('Configure uma SECRET_KEY segura em produção.')
ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '*').split(',') if host.strip()]

# ============================================================
# Frontend autorizado
# ============================================================

FRONTEND_URLS = [
    url.strip().rstrip('/')
    for url in os.getenv('FRONTEND_URLS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
    if url.strip()
]

CLOUDINARY_URL = os.getenv('CLOUDINARY_URL')

CORS_ALLOWED_ORIGINS = FRONTEND_URLS
CSRF_TRUSTED_ORIGINS = FRONTEND_URLS
CORS_ALLOW_CREDENTIALS = True

# ============================================================
# Aplicações instaladas
# ============================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Terceiros
    'corsheaders',
    'django_extensions',
    'django_filters',
    'drf_spectacular',
    'rest_framework',
    # Aplicações do projeto
    'uploader',
    'core',
]

# ============================================================
# Middlewares
# ============================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============================================================
# URLs
# ============================================================

ROOT_URLCONF = 'app.urls'
WSGI_APPLICATION = 'app.wsgi.application'

# ============================================================
# Templates
# ============================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ============================================================
# Banco de dados
# ============================================================

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ============================================================
# Validação de senhas
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============================================================
# Internacionalização
# ============================================================

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# ============================================================
# Arquivos estáticos
# ============================================================

STATIC_URL = '/static/'

# ============================================================
# Arquivos enviados pelos usuários
# ============================================================

MEDIA_ENDPOINT = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
FILE_UPLOAD_PERMISSIONS = 0o640

# Durante o desenvolvimento o frontend precisa acessar
# diretamente o servidor Django.

MEDIA_URL = 'http://127.0.0.1:8000/media/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ============================================================
# Cloudinary (opcional)
# ============================================================

if CLOUDINARY_URL:
    # Em produção, os arquivos enviados ficam armazenados
    # no Cloudinary.

    INSTALLED_APPS += [
        'cloudinary',
        'cloudinary_storage',
    ]

    MEDIA_URL = '/media/'
    STORAGES = {
        'default': {
            'BACKEND': 'uploader.storage.MediaCloudinaryStorage',
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }

# ============================================================
# Modelo padrão de chave primária
# ============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================
# Modelo de usuário
# ============================================================

AUTH_USER_MODEL = 'core.User'

# ============================================================
# Django REST Framework
# ============================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'app.pagination.CustomPagination',
    'PAGE_SIZE': 10,
}

# ============================================================
# OpenAPI / Swagger
# ============================================================

SPECTACULAR_SETTINGS = {
    'TITLE': 'Hackathon 2026 API',
    'DESCRIPTION': 'Gerenciamento colaborativo de projetos, membros, tarefas, Kanban, prazos e recursos.',
    'VERSION': '1.0.0',
}

# ============================================================
# Simple JWT
# ============================================================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=3),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ============================================================
# Notificações por e-mail
# ============================================================

NOTIFICATION_EMAIL_ENABLED = os.getenv('NOTIFICATION_EMAIL_ENABLED', 'False').lower() == 'true'
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'no-reply@hackathon.local')
