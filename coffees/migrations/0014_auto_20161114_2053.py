# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0013_auto_20161019_2314'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='coffeegear',
            options={'ordering': ['id']},
        ),
        migrations.AddField(
            model_name='coffeegear',
            name='special',
            field=models.CharField(blank=True, max_length=30, verbose_name='Special for', choices=[('set', 'Set')]),
        ),
    ]
