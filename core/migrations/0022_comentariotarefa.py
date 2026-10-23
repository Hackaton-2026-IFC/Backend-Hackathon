from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('core', '0021_atividade'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='ComentarioTarefa', fields=[
        ('id', models.BigAutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
        ('conteudo', models.TextField(max_length=5000)),
        ('criado_em', models.DateTimeField(auto_now_add=True)),
        ('atualizado_em', models.DateTimeField(auto_now=True)),
        ('autor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='comentarios_tarefa', to=settings.AUTH_USER_MODEL)),
        ('tarefa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comentarios', to='core.tarefa')),
    ], options={'ordering': ['criado_em', 'id']})]
