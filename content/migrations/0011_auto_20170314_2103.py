# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0010_instagrampost'),
    ]

    operations = [
        migrations.AlterField(
            model_name='greeting',
            name='line2',
            field=models.CharField(max_length=256, blank=True),
        ),
        migrations.AlterField(
            model_name='greeting',
            name='line2_en',
            field=models.CharField(max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='greeting',
            name='line2_zh_hans',
            field=models.CharField(max_length=256, null=True, blank=True),
        ),
    ]
