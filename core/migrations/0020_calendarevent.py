from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('core', '0019_tarefa_clima'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='CalendarEvent', fields=[
        ('id', models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
        ('titulo', models.CharField(max_length=150)),
        ('descricao', models.TextField(blank=True, default='')),
        ('data', models.DateField()),
        ('hora_inicio', models.TimeField(null=True, blank=True)),
        ('hora_fim', models.TimeField(null=True, blank=True)),
        ('localizacao', models.CharField(blank=True, default='', max_length=255)),
        ('criado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
        ('projeto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eventos', to='core.projeto')),
    ], options={'ordering': ['data', 'hora_inicio', 'id']})]
