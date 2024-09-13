# Generated by Django 5.0.8 on 2024-09-12 07:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('building', '0003_expense_building_expense_entrance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='building',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expense', to='building.building'),
        ),
        migrations.AlterField(
            model_name='expense',
            name='entrance',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expense', to='building.entrance'),
        ),
    ]