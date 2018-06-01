# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0011_rawbean'),
    ]

    operations = [
        migrations.AddField(
            model_name='rawbean',
            name='created_date',
            field=models.DateTimeField(default=datetime.datetime(2016, 10, 4, 17, 38, 32, 611150, tzinfo=utc), verbose_name=b'Created Date', auto_now_add=True),
            preserve_default=False,
        ),
    ]
