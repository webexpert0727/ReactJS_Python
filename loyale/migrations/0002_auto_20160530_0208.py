# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('loyale', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderpoints',
            name='one_pod',
            field=models.IntegerField(default=50, help_text=b'Nespresso alacarte', verbose_name=b'One-off shotpod'),
        ),
        migrations.AddField(
            model_name='orderpoints',
            name='sub_pod',
            field=models.IntegerField(default=200, help_text=b'Nespresso subscription', verbose_name=b'Subsequent shotpod'),
        ),
    ]
