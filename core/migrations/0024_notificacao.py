from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0023_nota'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notificacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(max_length=40)),
                ('titulo', models.CharField(max_length=180)),
                ('mensagem', models.TextField(blank=True, default='')),
                ('link', models.CharField(blank=True, default='', max_length=300)),
                ('lida_em', models.DateTimeField(blank=True, null=True)),
                ('email_enviado', models.BooleanField(default=False)),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('ator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notificacoes_geradas', to=settings.AUTH_USER_MODEL)),
                ('destinatario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notificacoes', to=settings.AUTH_USER_MODEL)),
                ('projeto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notificacoes', to='core.projeto')),
                ('tarefa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notificacoes', to='core.tarefa')),
            ],
            options={'ordering': ['-criada_em', '-id']},
        ),
        migrations.AddIndex(
            model_name='notificacao',
            index=models.Index(fields=['destinatario', 'lida_em', 'criada_em'], name='core_notifi_destina_67c95d_idx'),
        ),
    ]
