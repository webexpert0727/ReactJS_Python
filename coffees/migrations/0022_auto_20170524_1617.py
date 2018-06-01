# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0021_auto_20170513_0051'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='coffeegear',
            options={'ordering': ['the_order']},
        ),
        migrations.AddField(
            model_name='coffeegear',
            name='the_order',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
    ]
