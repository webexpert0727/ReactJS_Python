# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0019_coffeetype_blend'),
    ]

    operations = [
        migrations.AddField(
            model_name='coffeetype',
            name='discovery',
            field=models.BooleanField(default=False, verbose_name='Discovery programme'),
        ),
    ]
