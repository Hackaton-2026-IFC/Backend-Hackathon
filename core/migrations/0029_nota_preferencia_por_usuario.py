from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrar_fixacoes_autores(apps, schema_editor):
    Nota = apps.get_model('core', 'Nota')
    Preferencia = apps.get_model('core', 'NotaPreferencia')
    db_alias = schema_editor.connection.alias
    PreferenceBatch = [
        Preferencia(nota_id=note.pk, usuario_id=note.usuario_id, fixada=True)
        for note in Nota.objects.using(db_alias).filter(fixada=True).iterator()
    ]
    Preferencia.objects.using(db_alias).bulk_create(PreferenceBatch, ignore_conflicts=True, batch_size=500)


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0028_reconvite_apos_saida'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NotaPreferencia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fixada', models.BooleanField(default=False)),
                ('ordem', models.PositiveIntegerField(blank=True, null=True)),
                ('nota', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preferencias', to='core.nota')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preferencias_notas', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='notapreferencia',
            constraint=models.UniqueConstraint(fields=('nota', 'usuario'), name='nota_preferencia_por_usuario_unica'),
        ),
        migrations.RunPython(migrar_fixacoes_autores, migrations.RunPython.noop),
    ]
