# Generated by Django 5.0.3 on 2024-08-25 12:09

import datetime
import django.db.models.deletion
import month.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Building',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('address', models.CharField(max_length=100)),
                ('num_of_entrances', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Apartment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('floor', models.IntegerField()),
                ('number', models.IntegerField()),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owner', to=settings.AUTH_USER_MODEL)),
                ('building', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='building.building')),
            ],
        ),
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('electricity', models.FloatField()),
                ('cleaning', models.FloatField()),
                ('elevator_electricity', models.FloatField()),
                ('elevator_maintenance', models.FloatField()),
                ('entrance_maintenance', models.FloatField(default=10)),
                ('for_month', month.models.MonthField(default=datetime.datetime(2024, 8, 25, 15, 9, 13, 279624), null=True, verbose_name='Month')),
                ('is_paid', models.BooleanField(default=False)),
                ('apartment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='building.apartment')),
            ],
        ),
        migrations.CreateModel(
            name='Entrance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('floors', models.IntegerField()),
                ('num_of_apartments', models.IntegerField()),
                ('building', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='building.building')),
            ],
        ),
        migrations.AddField(
            model_name='apartment',
            name='entrance',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='building.entrance'),
        ),
    ]
