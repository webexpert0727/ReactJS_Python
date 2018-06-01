# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('loyale', '0004_item_in_stock'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='redemitem',
            options={'ordering': ['-shipping_date'], 'verbose_name': 'Orders', 'verbose_name_plural': 'Orders'},
        ),
    ]
