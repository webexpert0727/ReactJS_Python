# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0014_auto_20161114_2053'),
    ]

    operations = [
        migrations.AddField(
            model_name='coffeegear',
            name='allow_choice_package',
            field=models.BooleanField(default=False, help_text='Can a customer choose a package/brew method?', verbose_name='Allow the choice of packaging'),
        ),
    ]
