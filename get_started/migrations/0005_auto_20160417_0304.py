# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('get_started', '0004_giftvoucher'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='giftvoucher',
            name='sender',
        ),
        migrations.AddField(
            model_name='giftvoucher',
            name='sender_email',
            field=models.CharField(default='default@mail.com', max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='giftvoucher',
            name='sender_fname',
            field=models.CharField(default='Elton', max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='giftvoucher',
            name='sender_lname',
            field=models.CharField(default='John', max_length=64),
            preserve_default=False,
        ),
    ]
