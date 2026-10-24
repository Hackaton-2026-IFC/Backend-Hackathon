from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0024_notificacao'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlertaPrazo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(max_length=24)),
                ('prazo', models.DateField()),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('tarefa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alertas_prazo', to='core.tarefa')),
                ('destinatario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='alertaprazo',
            constraint=models.UniqueConstraint(fields=('tarefa', 'destinatario', 'tipo', 'prazo'), name='unique_alerta_prazo_tarefa_usuario_tipo_data'),
        ),
    ]
