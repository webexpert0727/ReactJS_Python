# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0030_auto_20170520_1535'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customer',
            options={'default_permissions': ('add', 'change', 'export', 'delete')},
        ),
        migrations.AlterModelOptions(
            name='gearorder',
            options={'ordering': ['-shipping_date'], 'default_permissions': ('add', 'change', 'export', 'delete')},
        ),
        migrations.AlterModelOptions(
            name='order',
            options={'ordering': ['-shipping_date'], 'default_permissions': ('add', 'change', 'export', 'delete')},
        ),
        migrations.AlterModelOptions(
            name='preferences',
            options={'default_permissions': ('add', 'change', 'export', 'delete'), 'verbose_name_plural': 'Preferences'},
        ),
    ]
