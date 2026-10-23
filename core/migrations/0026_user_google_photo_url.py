from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0025_alertaprazo')]

    operations = [
        migrations.AddField(
            model_name='user',
            name='google_photo_url',
            field=models.URLField(blank=True, default='', max_length=1000),
        ),
    ]
