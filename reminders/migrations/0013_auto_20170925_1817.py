# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-09-25 10:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reminders', '0012_remindersms'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='remindersms',
            name='number',
        ),
        migrations.AlterField(
            model_name='remindersms',
            name='message',
            field=models.CharField(max_length=612),
        ),
    ]
