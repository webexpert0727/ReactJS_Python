# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0014_auto_20160829_0110'),
    ]

    operations = [
        migrations.CreateModel(
            name='FYPOrderStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name=b'Order time')),
                ('order', models.ForeignKey(to='customers.Order')),
            ],
        ),
    ]
