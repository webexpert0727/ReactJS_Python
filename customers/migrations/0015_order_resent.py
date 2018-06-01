# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0014_auto_20160829_0110'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='resent',
            field=models.BooleanField(default=False, verbose_name=b'Resent Order?'),
        ),
    ]
