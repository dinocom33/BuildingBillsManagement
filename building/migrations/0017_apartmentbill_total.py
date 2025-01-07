# Generated by Django 5.1.4 on 2025-01-06 13:42

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('building', '0016_message_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='apartmentbill',
            name='total',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
    ]
