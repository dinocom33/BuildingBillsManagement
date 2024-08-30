# Generated by Django 5.0.3 on 2024-08-30 13:59

import month.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('building', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='apartmentbill',
            options={'ordering': ['-for_month', 'apartment']},
        ),
        migrations.AlterModelOptions(
            name='bill',
            options={'ordering': ['-for_month']},
        ),
        migrations.AddField(
            model_name='bill',
            name='for_month',
            field=month.models.MonthField(null=True, verbose_name='Month'),
        ),
    ]
