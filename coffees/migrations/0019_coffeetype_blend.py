# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0018_auto_20170312_0258'),
    ]

    operations = [
        migrations.AddField(
            model_name='coffeetype',
            name='blend',
            field=models.BooleanField(default=False, verbose_name='Blend'),
        ),
    ]
