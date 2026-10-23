from django.db import migrations


class Migration(migrations.Migration):
    # Unifica os dois caminhos criados paralelamente pelas FEAT-4 e FEAT-5.
    # Ambas as migrations anteriores continuam preservadas.
    dependencies = [
        ('core', '0012_projeto_status_prazo'),
        ('core', '0012_tarefa_dependencias'),
    ]

    operations = []
