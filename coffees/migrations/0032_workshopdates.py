# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2018-04-03 11:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0031_auto_20180402_1401'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkShopDates',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('status', models.BooleanField(default=True, verbose_name='Open')),
                ('workshop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='coffees.WorkShops')),
            ],
        ),
    ]
