# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0005_auto_20161019_2314'),
    ]

    operations = [
        migrations.CreateModel(
            name='BrewGuide',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=20)),
                ('name_en', models.CharField(max_length=20, null=True)),
                ('name_zh_hans', models.CharField(max_length=20, null=True)),
                ('description', models.TextField()),
                ('description_en', models.TextField(null=True)),
                ('description_zh_hans', models.TextField(null=True)),
                ('video', models.CharField(max_length=20)),
                ('required_list', models.TextField()),
                ('required_list_en', models.TextField(null=True)),
                ('required_list_zh_hans', models.TextField(null=True)),
                ('brew_time', models.CharField(default='30 seconds', max_length=50)),
                ('brew_time_en', models.CharField(default='30 seconds', max_length=50, null=True)),
                ('brew_time_zh_hans', models.CharField(default='30 seconds', max_length=50, null=True)),
                ('img', models.ImageField(upload_to=b'')),
                ('banner', models.ImageField(upload_to=b'')),
            ],
        ),
        migrations.CreateModel(
            name='BrewGuideStep',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('img', models.ImageField(null=True, upload_to=b'', blank=True)),
                ('description', models.TextField()),
                ('description_en', models.TextField(null=True)),
                ('description_zh_hans', models.TextField(null=True)),
                ('brew_guide', models.ForeignKey(related_name='steps', to='content.BrewGuide')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
    ]
