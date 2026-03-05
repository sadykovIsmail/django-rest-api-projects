from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('author', '0003_alter_blogpostmodel_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogpostmodel',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='posts/'),
        ),
    ]
