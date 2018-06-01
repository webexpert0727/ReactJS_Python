# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0033_auto_20170629_0225'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='package',
            field=models.CharField(default='GR', max_length=16, verbose_name='Packaging method', choices=[('GR', 'Ground (200g)'), ('WB', 'Wholebeans (200g)'), ('DR', 'Drip bags (x10)'), ('BO', 'Bottled (x6)')]),
        ),
        migrations.AlterField(
            model_name='preferences',
            name='package',
            field=models.CharField(default='WB', max_length=16, verbose_name='Packaging method', choices=[('GR', 'Ground (200g)'), ('WB', 'Wholebeans (200g)'), ('DR', 'Drip bags (x10)'), ('BO', 'Bottled (x6)')]),
        ),
    ]
