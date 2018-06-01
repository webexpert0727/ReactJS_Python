# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0023_auto_20170402_1918'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gearorder',
            name='voucher',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='customers.Voucher', null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='voucher',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='customers.Voucher', null=True),
        ),
    ]
