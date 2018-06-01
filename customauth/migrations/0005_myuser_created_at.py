# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customauth', '0004_auto_20161122_0108'),
    ]

    operations = [
        migrations.AddField(
            model_name='myuser',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
