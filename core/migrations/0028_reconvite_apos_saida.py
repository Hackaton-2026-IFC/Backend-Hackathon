from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0027_nota_multimidia'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='conviteprojeto',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='conviteprojeto',
            constraint=models.UniqueConstraint(
                fields=('projeto', 'usuario'),
                condition=models.Q(status='pendente'),
                name='unique_convite_pendente_por_projeto',
            ),
        ),
    ]
