# Generated by Django 5.0.8 on 2024-09-12 09:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('building', '0009_alter_expense_maintenance_total_amount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='maintenance_total_amount',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expense', to='building.totalmaintenanceamount'),
        ),
    ]
