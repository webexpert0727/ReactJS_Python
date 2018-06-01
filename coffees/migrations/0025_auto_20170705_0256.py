# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0024_coffeetype_unavailable'),
    ]

    operations = [
        migrations.AddField(
            model_name='coffeetype',
            name='img_moreinfo',
            field=models.ImageField(null=True, upload_to=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='coffeetype',
            name='label_position',
            field=models.IntegerField(default=1, verbose_name='Position', choices=[(1, 'Left'), (2, 'Right')]),
        ),
    ]
