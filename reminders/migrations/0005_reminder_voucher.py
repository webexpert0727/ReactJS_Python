# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0025_auto_20170419_0421'),
        ('reminders', '0004_auto_20170111_0148'),
    ]

    operations = [
        migrations.AddField(
            model_name='reminder',
            name='voucher',
            field=models.ForeignKey(blank=True, to='customers.Voucher', null=True),
        ),
    ]
