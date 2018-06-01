# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0013_facebookcustomer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='package',
            field=models.CharField(default=b'GR', max_length=16, verbose_name=b'Packaging method', choices=[(b'GR', b'Grounded (200g)'), (b'WB', b'Wholebeans (200g)'), (b'DR', b'Drip bags (x10)')]),
        ),
        migrations.AlterField(
            model_name='preferences',
            name='package',
            field=models.CharField(default=b'WB', max_length=16, verbose_name=b'Packaging method', choices=[(b'GR', b'Grounded (200g)'), (b'WB', b'Wholebeans (200g)'), (b'DR', b'Drip bags (x10)')]),
        ),
    ]
