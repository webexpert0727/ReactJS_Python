# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_hstore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0020_auto_20161128_0558'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='extra',
            field=django_hstore.fields.DictionaryField(default={}, null=True, editable=False),
        ),
    ]
