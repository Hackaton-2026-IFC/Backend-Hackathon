import os
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = 'Valida configuração de deploy e conectividade do banco, sem exibir segredos.'

    def handle(self, *args, **options):
        problems = []
        if settings.DEBUG:
            problems.append('DEBUG deve ser False em produção.')
        if not settings.SECRET_KEY or settings.SECRET_KEY == 'django-insecure':
            problems.append('SECRET_KEY segura não configurada.')
        if not settings.ALLOWED_HOSTS or '*' in settings.ALLOWED_HOSTS:
            problems.append('ALLOWED_HOSTS deve listar os domínios da aplicação.')
        if not settings.CORS_ALLOWED_ORIGINS:
            problems.append('FRONTEND_URLS/CORS_ALLOWED_ORIGINS está vazio.')
        for origin in settings.CORS_ALLOWED_ORIGINS:
            parsed = urlparse(origin)
            if parsed.scheme not in ('http', 'https') or not parsed.netloc:
                problems.append('Há uma origem CORS inválida.')
            if not settings.DEBUG and parsed.scheme != 'https':
                problems.append('Todas as origens CORS devem usar HTTPS em produção.')
        try:
            connection.ensure_connection()
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                cursor.fetchone()
        except Exception as exc:
            problems.append(f'Falha na conectividade do banco: {type(exc).__name__}')
        if problems:
            raise CommandError('Falha nas verificações de produção:\n- ' + '\n- '.join(problems))
        self.stdout.write(self.style.SUCCESS('Verificações de produção OK (configuração e banco).'))
