# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_hstore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0005_customer_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='details',
            field=django_hstore.fields.DictionaryField(default={}),
        ),
    ]
