# Generated by Django 5.0.9 on 2024-11-25 10:08

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('building', '0013_message'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='apartment',
            unique_together={('number', 'building', 'entrance', 'floor', 'owner')},
        ),
        migrations.AlterUniqueTogether(
            name='building',
            unique_together={('number', 'address')},
        ),
        migrations.AlterUniqueTogether(
            name='entrance',
            unique_together={('name', 'building')},
        ),
    ]