from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_add_banner_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='banner_image',
            field=models.ImageField(
                blank=True,
                help_text='Profile banner image (recommended: 1400×350px)',
                null=True,
                upload_to='user_banners/',
            ),
        ),
    ]
