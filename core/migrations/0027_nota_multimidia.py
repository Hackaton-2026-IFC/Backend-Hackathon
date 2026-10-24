from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0026_user_google_photo_url')]

    operations = [
        migrations.AddField(
            model_name='nota',
            name='link',
            field=models.URLField(blank=True, default='', max_length=2000),
        ),
        migrations.AddField(
            model_name='nota',
            name='imagem',
            field=models.ImageField(blank=True, null=True, upload_to='notas/imagens/%Y/%m/'),
        ),
    ]
