# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0025_auto_20170419_0421'),
    ]

    operations = [
        migrations.AddField(
            model_name='voucher',
            name='email',
            field=models.CharField(default='', max_length=64, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='voucher',
            name='personal',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='order',
            name='package',
            field=models.CharField(default='GR', max_length=16, verbose_name='Packaging method', choices=[('GR', 'Ground (200g)'), ('WB', 'Wholebeans (200g)'), ('DR', 'Drip bags (x10)')]),
        ),
        migrations.AlterField(
            model_name='preferences',
            name='package',
            field=models.CharField(default='WB', max_length=16, verbose_name='Packaging method', choices=[('GR', 'Ground (200g)'), ('WB', 'Wholebeans (200g)'), ('DR', 'Drip bags (x10)')]),
        ),
    ]
