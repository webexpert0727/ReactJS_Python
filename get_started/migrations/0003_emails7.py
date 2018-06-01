# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('get_started', '0002_emails24'),
    ]

    operations = [
        migrations.CreateModel(
            name='Emails7',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(max_length=32)),
                ('email', models.EmailField(max_length=254)),
                ('time', models.DateTimeField()),
            ],
        ),
    ]
