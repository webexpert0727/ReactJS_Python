# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0022_auto_20170524_1617'),
        ('reminders', '0005_reminder_voucher'),
    ]

    operations = [
        migrations.AddField(
            model_name='reminder',
            name='recommended_coffee',
            field=models.ForeignKey(blank=True, to='coffees.CoffeeType', null=True),
        ),
    ]
