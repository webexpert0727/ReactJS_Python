# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-11-17 16:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0006_auto_20171118_0043'),
    ]

    operations = [
        migrations.AddField(
            model_name='roadbullorder',
            name='bar_code_url',
            field=models.CharField(default='', max_length=128),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='roadbullorder',
            name='label_pdf',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='roadbullorder',
            name='qr_code_url',
            field=models.CharField(default='', max_length=128),
            preserve_default=False,
        ),
    ]
