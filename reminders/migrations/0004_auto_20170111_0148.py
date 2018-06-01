# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reminders', '0003_auto_20161122_0108'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reminder',
            name='from_email',
            field=models.CharField(default='Hook Coffee <hola@hookcoffee.com.sg>', max_length=100),
        ),
    ]
