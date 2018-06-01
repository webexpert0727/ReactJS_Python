# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0019_order_custom_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='country',
            field=django_countries.fields.CountryField(default='SG', max_length=2),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='customer',
            name='postcode',
            field=models.CharField(max_length=13, verbose_name='Postal code'),
        ),
    ]
