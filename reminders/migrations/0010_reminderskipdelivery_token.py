# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-09-06 10:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reminders', '0009_auto_20170816_2118'),
    ]

    operations = [
        migrations.AddField(
            model_name='reminderskipdelivery',
            name='token',
            field=models.CharField(default='dummy', max_length=64),
            preserve_default=False,
        ),
    ]
