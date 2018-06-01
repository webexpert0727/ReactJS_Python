# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0006_brewguide_brewguidestep'),
    ]

    operations = [
        migrations.AddField(
            model_name='brewguide',
            name='slug',
            field=models.SlugField(default='', unique=True, max_length=20),
            preserve_default=False,
        ),
    ]
