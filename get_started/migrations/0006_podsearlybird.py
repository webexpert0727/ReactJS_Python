# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('get_started', '0005_auto_20160417_0304'),
    ]

    operations = [
        migrations.CreateModel(
            name='PodsEarlyBird',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.CharField(max_length=64)),
                ('date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
