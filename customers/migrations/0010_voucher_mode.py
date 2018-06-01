# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0009_auto_20160417_0304'),
    ]

    operations = [
        migrations.AddField(
            model_name='voucher',
            name='mode',
            field=models.BooleanField(default=True, verbose_name=b'Enabled'),
        ),
    ]
