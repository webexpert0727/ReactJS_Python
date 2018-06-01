# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0016_auto_20161128_0558'),
    ]

    operations = [
        migrations.AddField(
            model_name='coffeegear',
            name='available',
            field=models.BooleanField(default=True, verbose_name='Available'),
        ),
    ]
