from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('core', '0014_projetofixado')]
    operations = [
        migrations.AddField(model_name='projeto', name='prazo_antecipado', field=models.DateField(null=True, blank=True)),
        migrations.AddField(model_name='tarefa', name='prazo_antecipado', field=models.DateField(null=True, blank=True)),
    ]
