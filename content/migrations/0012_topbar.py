# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0011_auto_20170314_2103'),
    ]

    operations = [
        migrations.CreateModel(
            name='TopBar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('block_text', models.CharField(max_length=256)),
                ('button_text', models.CharField(help_text='Leave this field blank if you want to make the text clickable (the text will be a link)', max_length=36, blank=True)),
                ('link', models.URLField(max_length=256)),
                ('visible', models.BooleanField(default=False)),
            ],
        ),
    ]
