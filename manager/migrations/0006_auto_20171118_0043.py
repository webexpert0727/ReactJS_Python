# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-11-17 16:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0005_roadbullorder'),
    ]

    operations = [
        migrations.AlterField(
            model_name='roadbullorder',
            name='consignment_number',
            field=models.CharField(max_length=32),
        ),
        migrations.AlterField(
            model_name='roadbullorder',
            name='order_number',
            field=models.CharField(max_length=32),
        ),
        migrations.AlterField(
            model_name='roadbullorder',
            name='tracking_number',
            field=models.CharField(max_length=32),
        ),
    ]
