# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0029_postcard'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='interval',
            field=models.PositiveIntegerField(default=14, verbose_name='Shipping Interval'),
        ),
    ]
