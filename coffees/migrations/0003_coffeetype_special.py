# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0002_coffeetype_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='coffeetype',
            name='special',
            field=models.BooleanField(default=False, verbose_name=b'Special'),
        ),
    ]
