from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('core', '0020_calendarevent'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='Atividade', fields=[
        ('id', models.BigAutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
        ('tarefa_id_original', models.BigIntegerField(null=True, blank=True, db_index=True)),
        ('tarefa_titulo', models.CharField(max_length=150, blank=True, default='')),
        ('acao', models.CharField(max_length=40)),
        ('alteracoes', models.JSONField(default=dict, blank=True)),
        ('criado_em', models.DateTimeField(auto_now_add=True)),
        ('autor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='atividades', to=settings.AUTH_USER_MODEL)),
        ('projeto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='atividades', to='core.projeto')),
        ('tarefa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='atividades', to='core.tarefa')),
    ], options={'ordering':['-criado_em','-id']})]
