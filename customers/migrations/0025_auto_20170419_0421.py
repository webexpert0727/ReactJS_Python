# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0024_auto_20170412_1944'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shoppingcart',
            name='voucher',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='customers.Voucher'),
        ),
    ]
