# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0002_auto_20160118_0333'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='card_details',
            field=models.CharField(default=b'0000000000', max_length=10, null=True, blank=True),
        ),
    ]
