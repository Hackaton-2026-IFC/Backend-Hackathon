from datetime import date

from django.core.management.base import BaseCommand, CommandError

from core.services.prazos import processar_alertas_prazo


class Command(BaseCommand):
    help = 'Gera alertas de tarefas que vencem amanhã, hoje ou estão atrasadas.'

    def add_arguments(self, parser):
        parser.add_argument('--data', help='Data de simulação YYYY-MM-DD (apenas para testes administrativos).')

    def handle(self, *args, **options):
        try:
            hoje = date.fromisoformat(options['data']) if options.get('data') else None
        except ValueError as exc:
            raise CommandError('Informe uma data no formato YYYY-MM-DD.') from exc
        result = processar_alertas_prazo(hoje)
        self.stdout.write(self.style.SUCCESS(f'Alertas gerados: {result}'))
