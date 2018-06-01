# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('loyale', '0002_auto_20160530_0208'),
    ]

    operations = [
        migrations.CreateModel(
            name='Helper',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('emails_rewards_sent', models.BooleanField(default=False, verbose_name=b'Were sent?')),
                ('emails_rewards_sent_count', models.IntegerField(default=0, verbose_name=b'Emails sent last time')),
            ],
        ),
    ]
