# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reminders', '0002_data_migration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reminder',
            name='from_email',
            field=models.CharField(default='Hook Coffee <orders@hookcoffee.com.sg>', max_length=100),
        ),
    ]
