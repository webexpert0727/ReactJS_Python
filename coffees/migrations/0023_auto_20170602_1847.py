# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0022_auto_20170524_1617'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coffeetype',
            name='more_taste',
            field=models.CharField(max_length=512, verbose_name='More taste'),
        ),
        migrations.AlterField(
            model_name='coffeetype',
            name='more_taste_en',
            field=models.CharField(max_length=512, null=True, verbose_name='More taste'),
        ),
        migrations.AlterField(
            model_name='coffeetype',
            name='more_taste_zh_hans',
            field=models.CharField(max_length=512, null=True, verbose_name='More taste'),
        ),
    ]
