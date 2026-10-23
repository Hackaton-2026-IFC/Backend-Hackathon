from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('core', '0018_googleidentity')]
    operations = [
        migrations.AddField(model_name='tarefa', name='clima_influencia', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='tarefa', name='localizacao', field=models.CharField(blank=True, default='', max_length=255)),
    ]
