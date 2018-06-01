# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0004_auto_20160403_2048'),
    ]

    operations = [
        migrations.CreateModel(
            name='CoffeeGear',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name=b'Title')),
                ('essentials', models.BooleanField(default=True, verbose_name=b'Essentials')),
                ('model', models.CharField(max_length=32, verbose_name=b'Model')),
                ('description', models.CharField(max_length=512, verbose_name=b'Description')),
                ('link', models.CharField(default=b'#', max_length=256, verbose_name=b'Watch brew guide link')),
                ('price', models.DecimalField(verbose_name=b'Price', max_digits=6, decimal_places=2)),
                ('img', models.ImageField(upload_to=b'')),
            ],
        ),
    ]
