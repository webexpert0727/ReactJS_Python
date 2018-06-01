# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0011_auto_20160530_0208'),
        ('coffees', '0006_coffeesticker'),
    ]

    operations = [
        migrations.CreateModel(
            name='SharedCoffeeSticker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.BigIntegerField(verbose_name=b'User')),
                ('post', models.BigIntegerField(verbose_name=b'Post')),
                ('hashtag', models.CharField(max_length=256, verbose_name=b'Shared hashtag', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'Created')),
                ('customer', models.ForeignKey(blank=True, to='customers.Customer', null=True)),
            ],
        ),
    ]
