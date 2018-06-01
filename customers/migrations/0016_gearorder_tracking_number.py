# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0015_order_resent'),
    ]

    operations = [
        migrations.AddField(
            model_name='gearorder',
            name='tracking_number',
            field=models.CharField(max_length=30, blank=True),
        ),
    ]
