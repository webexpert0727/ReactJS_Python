# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0003_customer_card_details'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='feedback',
            field=models.CharField(blank=True, max_length=16, null=True, choices=[(b'UP', b'Happy'), (b'DOWN', b'Unhappy')]),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(default=b'AC', max_length=16, verbose_name=b'Status', choices=[(b'AC', b'Active'), (b'SH', b'Shipped'), (b'PA', b'Paused'), (b'CA', b'Canceled'), (b'ER', b'Failed'), (b'DE', b'Declined')]),
        ),
        migrations.AlterField(
            model_name='preferences',
            name='package',
            field=models.CharField(default=b'WB', max_length=16, verbose_name=b'Packaging method', choices=[(b'GR', b'Grounded (250g)'), (b'WB', b'Wholebeans (250g)'), (b'DR', b'Drip bags (x10)')]),
        ),
    ]
