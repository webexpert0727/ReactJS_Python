# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('loyale', '0003_helper'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='in_stock',
            field=models.BooleanField(default=True, verbose_name='In Stock'),
        ),
    ]
