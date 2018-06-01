# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0031_auto_20170609_0425'),
    ]

    operations = [
        migrations.CreateModel(
            name='CardFingerprint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fingerprint', models.CharField(max_length=128, verbose_name='Card fingerprint')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='customers.Customer', null=True)),
            ],
        ),
    ]
