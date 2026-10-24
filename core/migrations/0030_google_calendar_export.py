from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0029_nota_preferencia_por_usuario'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GoogleCalendarExport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('google_event_id', models.CharField(max_length=255)),
                ('google_event_url', models.URLField(blank=True, default='', max_length=2000)),
                ('exportado_em', models.DateTimeField(auto_now_add=True)),
                ('evento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exportacoes_google', to='core.calendarevent')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exportacoes_google_agenda', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='googlecalendarexport',
            constraint=models.UniqueConstraint(fields=['evento', 'usuario'], name='google_agenda_evento_usuario_unico'),
        ),
    ]
