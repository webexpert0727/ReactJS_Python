# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0007_brewguide_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='brewguide',
            name='banner_img_bcolor',
            field=models.CharField(default='#eeeeee', help_text='Background color (in HEX format) for right part', max_length=7),
        ),
        migrations.AddField(
            model_name='brewguide',
            name='banner_txt_bcolor',
            field=models.CharField(default='#eeeeee', help_text='Background color (in HEX format) for left part', max_length=7),
        ),
        migrations.AddField(
            model_name='brewguide',
            name='subtitle',
            field=models.CharField(max_length=20, blank=True),
        ),
        migrations.AddField(
            model_name='brewguide',
            name='subtitle_en',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='brewguide',
            name='subtitle_zh_hans',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),
    ]
