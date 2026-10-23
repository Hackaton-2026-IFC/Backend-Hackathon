from django.db import migrations, models


def migrar_status_existente(apps, schema_editor):
    Tarefa = apps.get_model('core', 'Tarefa')
    Tarefa.objects.filter(concluida=True).update(status='concluido')


class Migration(migrations.Migration):
    dependencies = [('core', '0011_tarefa_status_microtarefa')]

    operations = [
        migrations.AddField(
            model_name='tarefa',
            name='dependencias',
            field=models.ManyToManyField(blank=True, related_name='tarefas_dependentes', symmetrical=False, to='core.tarefa'),
        ),
        migrations.RunPython(migrar_status_existente, migrations.RunPython.noop),
    ]
