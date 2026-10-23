from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0011_membros_cargo_member'),
    ]

    operations = [
        migrations.AddField(
            model_name='projeto',
            name='status',
            field=models.CharField(
                choices=[
                    ('planejado', 'Planejado'),
                    ('em_andamento', 'Em andamento'),
                    ('concluido', 'Concluído'),
                ],
                default='planejado',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='projeto',
            name='data_limite',
            field=models.DateField(blank=True, null=True),
        ),
    ]
