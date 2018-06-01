# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_hstore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0017_customer_received_coffee_samples'),
    ]

    operations = [
        migrations.AddField(
            model_name='gearorder',
            name='voucher',
            field=models.ForeignKey(blank=True, to='customers.Voucher', null=True),
        ),
        migrations.AlterField(
            model_name='gearorder',
            name='details',
            field=django_hstore.fields.DictionaryField(null=True, editable=False),
        ),
    ]
