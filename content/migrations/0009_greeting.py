# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0008_auto_20161111_0413'),
    ]

    operations = [
        migrations.CreateModel(
            name='Greeting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_of_day', models.CharField(max_length=16)),
                ('line1', models.CharField(max_length=128)),
                ('line1_en', models.CharField(max_length=128, null=True)),
                ('line1_zh_hans', models.CharField(max_length=128, null=True)),
                ('line2', models.CharField(max_length=256)),
                ('line2_en', models.CharField(max_length=256, null=True)),
                ('line2_zh_hans', models.CharField(max_length=256, null=True)),
                ('line3', models.CharField(max_length=512)),
                ('line3_en', models.CharField(max_length=512, null=True)),
                ('line3_zh_hans', models.CharField(max_length=512, null=True)),
            ],
        ),
    ]
