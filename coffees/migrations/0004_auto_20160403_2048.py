# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0003_coffeetype_special'),
    ]

    operations = [
        migrations.AddField(
            model_name='coffeetype',
            name='label',
            field=models.FileField(upload_to=b'labels/', blank=True),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='label_drip',
            field=models.FileField(upload_to=b'labels/', blank=True),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='label_position',
            field=models.IntegerField(default=1, verbose_name=b'Position', choices=[(1, b'Left'), (2, b'Right')]),
            preserve_default=False,
        ),
    ]
