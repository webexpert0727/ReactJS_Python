# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name=b'Title')),
                ('goal_1', models.CharField(max_length=128, verbose_name=b'Goal 1')),
                ('goal_2', models.CharField(max_length=128, verbose_name=b'Goal 2')),
                ('goal_2_note', models.CharField(default=None, max_length=128, null=True, verbose_name=b'Goal 2 note', blank=True)),
                ('description_1', models.CharField(max_length=128, verbose_name=b'Description 1')),
                ('description_2', models.CharField(max_length=128, verbose_name=b'Description 2')),
                ('description_2_note', models.CharField(default=None, max_length=128, null=True, verbose_name=b'Description 2 note', blank=True)),
                ('comments', models.CharField(max_length=256, verbose_name=b'Comments')),
                ('price', models.DecimalField(decimal_places=2, default=None, max_digits=6, blank=True, null=True, verbose_name=b'Price')),
                ('img', models.ImageField(upload_to=b'')),
            ],
        ),
    ]
