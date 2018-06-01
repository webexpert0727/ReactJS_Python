# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0013_auto_20161019_2314'),
        ('customers', '0016_gearorder_tracking_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='received_coffee_samples',
            field=models.ManyToManyField(related_name='+', to='coffees.CoffeeType', blank=True),
        ),
    ]
