# Generated by Django 5.0.8 on 2024-09-12 08:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('building', '0006_alter_expense_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='maintenance_total_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
