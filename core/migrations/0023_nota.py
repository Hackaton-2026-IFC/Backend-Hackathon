from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0022_comentariotarefa'),
    ]

    operations = [
        migrations.CreateModel(
            name='Nota',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(blank=True, default='', max_length=200)),
                ('conteudo', models.TextField(blank=True, default='')),
                ('cor', models.CharField(default='#FFF475', max_length=7)),
                ('fixada', models.BooleanField(default=False)),
                ('arquivada', models.BooleanField(default=False)),
                ('etiquetas', models.JSONField(blank=True, default=list)),
                ('lembrete_em', models.DateTimeField(blank=True, null=True)),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('atualizada_em', models.DateTimeField(auto_now=True)),
                ('projeto', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notas', to='core.projeto')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-fixada', '-atualizada_em', '-id'],
            },
        ),
        migrations.AddIndex(
            model_name='nota',
            index=models.Index(fields=['usuario', 'arquivada', 'fixada'], name='core_nota_usuario_012f10_idx'),
        ),
        migrations.AddIndex(
            model_name='nota',
            index=models.Index(fields=['usuario', 'projeto'], name='core_nota_usuario_38f65d_idx'),
        ),
    ]
