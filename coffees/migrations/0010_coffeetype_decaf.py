# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0009_coffeetype_intensity'),
    ]

    operations = [
        migrations.AddField(
            model_name='coffeetype',
            name='decaf',
            field=models.BooleanField(default=False, verbose_name=b'Decaffeinated'),
        ),
    ]
