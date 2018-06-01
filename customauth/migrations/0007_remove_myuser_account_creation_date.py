# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customauth', '0006_myuser_fill_created_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='myuser',
            name='account_creation_date',
        ),
    ]
