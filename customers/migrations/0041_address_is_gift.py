# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-10-16 13:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0040_auto_20170925_0348'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='is_gift',
            field=models.BooleanField(default=False),
        ),
    ]
