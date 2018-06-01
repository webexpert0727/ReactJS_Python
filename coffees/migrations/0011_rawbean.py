# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0010_coffeetype_decaf'),
    ]

    operations = [
        migrations.CreateModel(
            name='RawBean',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=256, verbose_name=b'Name')),
                ('stock', models.DecimalField(verbose_name=b'Amount', max_digits=6, decimal_places=2)),
                ('status', models.BooleanField(default=True, verbose_name=b'Available')),
            ],
        ),
    ]
