from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0016_tarefa_urgencia_manual'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Recurso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=150)),
                ('url', models.URLField(max_length=2000)),
                ('tipo', models.CharField(choices=[
                    ('documento', 'Documento'), ('pasta', 'Pasta'),
                    ('link', 'Link'), ('repositorio', 'Repositório'), ('outro', 'Outro'),
                ], default='link', max_length=20)),
                ('descricao', models.TextField(blank=True, default='')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('adicionado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recursos_adicionados', to=settings.AUTH_USER_MODEL)),
                ('projeto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recursos', to='core.projeto')),
                ('tarefa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='recursos', to='core.tarefa')),
            ],
            options={'ordering': ['-criado_em', '-id']},
        ),
    ]
