# Generated by Django 5.1.4 on 2025-01-06 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('building', '0017_apartmentbill_total'),
    ]

    operations = [
        migrations.AddField(
            model_name='apartmentbill',
            name='given_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
