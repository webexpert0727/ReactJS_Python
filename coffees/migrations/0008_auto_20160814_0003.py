# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0007_sharedcoffeesticker'),
    ]

    operations = [
        migrations.AddField(
            model_name='coffeetype',
            name='amount_one_off',
            field=models.DecimalField(default=18, verbose_name=b'Amount for One-off', max_digits=6, decimal_places=2),
        ),
        migrations.AlterField(
            model_name='coffeetype',
            name='amount',
            field=models.DecimalField(default=14, verbose_name=b'Amount', max_digits=6, decimal_places=2),
        ),
    ]
