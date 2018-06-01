# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0015_coffeegear_allow_choice_package'),
    ]

    operations = [
        migrations.DeleteModel(
            name='News',
        ),
        migrations.AddField(
            model_name='coffeegear',
            name='weight',
            field=models.IntegerField(default=500, verbose_name='Shipping weight'),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='weight',
            field=models.IntegerField(default=200, verbose_name='Shipping weight'),
        ),
    ]
