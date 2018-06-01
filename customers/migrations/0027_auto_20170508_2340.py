# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0026_auto_20170428_1403'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coffeereview',
            name='order',
            field=models.ForeignKey(related_name='reviews', to='customers.Order'),
        ),
        migrations.AlterUniqueTogether(
            name='coffeereview',
            unique_together=set([('order', 'coffee')]),
        ),
    ]
