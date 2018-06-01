# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wholesale', '0002_auto_20161019_2330'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='office_type',
            field=models.CharField(default=b'WO', max_length=48, null=True, blank=True, choices=[(b'W', b'Offices with a coffee machine'), (b'WO', b'Offices without a coffee machine')]),
        ),
    ]
