# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_hstore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0034_auto_20170705_0256'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='discounts',
            field=django_hstore.fields.DictionaryField(default={'referral': []}),
        ),
    ]
