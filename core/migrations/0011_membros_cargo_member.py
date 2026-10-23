from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0010_conviteprojeto')]

    operations = [
        migrations.AlterField(
            model_name='projetomembro',
            name='cargo',
            field=models.CharField(
                choices=[('owner', 'Owner'), ('admin', 'Admin'), ('member', 'Membro')],
                default='admin',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='conviteprojeto',
            name='cargo',
            field=models.CharField(
                choices=[('owner', 'Owner'), ('admin', 'Admin'), ('member', 'Membro')],
                default='admin',
                max_length=20,
            ),
        ),
    ]
