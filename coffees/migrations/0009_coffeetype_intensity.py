# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0008_auto_20160814_0003'),
    ]

    operations = [
        migrations.AddField(
            model_name='coffeetype',
            name='intensity',
            field=models.IntegerField(default=6, verbose_name=b'Intensity'),
        ),
    ]
