# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0012_topbar'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='is_workplace',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='review',
            name='logo',
            field=models.ImageField(null=True, upload_to=b'', blank=True),
        ),
    ]
