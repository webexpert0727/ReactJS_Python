# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('customauth', '0002_login'),
    ]

    operations = [
        migrations.AddField(
            model_name='myuser',
            name='account_creation_date',
            field=models.DateTimeField(default=datetime.datetime(2016, 9, 20, 19, 15, 55, 715094, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
    ]
