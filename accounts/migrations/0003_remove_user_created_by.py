# Generated by Django 5.0.9 on 2024-11-21 12:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_created_by'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='created_by',
        ),
    ]
