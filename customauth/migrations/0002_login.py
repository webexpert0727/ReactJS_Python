# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customauth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Login',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(max_length=32, verbose_name=b'Username')),
                ('password', models.CharField(max_length=255, verbose_name=b'Password')),
                ('accesstoken', models.CharField(max_length=255, verbose_name=b'Access Token')),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
