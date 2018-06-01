# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0018_auto_20161120_2357'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='custom_price',
            field=models.BooleanField(default=False, verbose_name='Custom Price?'),
        ),
    ]
