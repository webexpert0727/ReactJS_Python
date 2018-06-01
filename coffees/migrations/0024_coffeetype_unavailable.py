# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0023_auto_20170602_1847'),
    ]

    operations = [
        migrations.AddField(
            model_name='coffeetype',
            name='unavailable',
            field=models.BooleanField(default=False, verbose_name='Temporary unavailable'),
        ),
    ]
