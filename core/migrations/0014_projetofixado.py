from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('core', '0013_merge_projeto_tarefas')]
    operations = [
        migrations.CreateModel(
            name='ProjetoFixado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fixado_em', models.DateTimeField(auto_now_add=True)),
                ('projeto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fixacoes', to='core.projeto')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projetos_fixados', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='projetofixado',
            constraint=models.UniqueConstraint(fields=['usuario', 'projeto'], name='projeto_fixado_por_usuario_unico'),
        ),
    ]
