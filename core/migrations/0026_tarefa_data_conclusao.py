from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0025_alertaprazo'),
    ]

    operations = [
        migrations.AddField(
            model_name='tarefa',
            name='data_conclusao',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
    ]
