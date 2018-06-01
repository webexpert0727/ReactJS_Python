# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0027_auto_20170508_2340'),
    ]

    operations = [
        migrations.AddField(
            model_name='vouchercategory',
            name='desc',
            field=models.TextField(default='', help_text='(optional)', verbose_name='Description', blank=True),
        ),
    ]
