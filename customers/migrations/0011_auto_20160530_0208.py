# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0010_voucher_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='preferences',
            name='different_pods',
            field=models.BooleanField(default=False, verbose_name=b'Different Pods?'),
        ),
        migrations.AddField(
            model_name='preferences',
            name='force_coffee_pods',
            field=models.BooleanField(default=False, verbose_name=b'Force sending Pod choosen by client'),
        ),
        migrations.AddField(
            model_name='preferences',
            name='interval_pods',
            field=models.PositiveIntegerField(default=7, verbose_name=b'Shipping Interval for Pods'),
        ),
        migrations.AlterField(
            model_name='preferences',
            name='force_coffee',
            field=models.BooleanField(default=False, verbose_name=b'Force sending Bag choosen by client'),
        ),
    ]
