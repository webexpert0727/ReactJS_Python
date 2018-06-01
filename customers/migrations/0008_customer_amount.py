# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0007_auto_20160321_0122'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='amount',
            field=models.IntegerField(default=0, help_text=b'SGD', verbose_name=b'Credits'),
        ),
    ]
