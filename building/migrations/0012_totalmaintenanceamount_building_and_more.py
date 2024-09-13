# Generated by Django 5.0.8 on 2024-09-12 12:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('building', '0011_alter_totalmaintenanceamount_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='totalmaintenanceamount',
            name='building',
            field=models.ForeignKey(default=14, on_delete=django.db.models.deletion.CASCADE, related_name='total_maintenance_amount', to='building.building'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='totalmaintenanceamount',
            name='entrance',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, related_name='total_maintenance_amount', to='building.entrance'),
            preserve_default=False,
        ),
    ]