# Generated by Django 5.1.4 on 2024-12-18 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('building', '0015_alter_apartment_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='messages/files/'),
        ),
    ]
