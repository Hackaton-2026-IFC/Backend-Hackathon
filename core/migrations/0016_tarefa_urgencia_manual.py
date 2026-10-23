from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('core', '0015_prazos_antecipados')]
    operations = [
        migrations.AddField(
            model_name='tarefa', name='urgencia_manual',
            field=models.CharField(
                max_length=20, null=True, blank=True,
                choices=[
                    ('muito_baixa', 'Muito baixa'), ('baixa', 'Baixa'),
                    ('neutra', 'Neutra'), ('alta', 'Alta'),
                    ('muito_alta', 'Muito alta'),
                ],
            ),
        ),
    ]
