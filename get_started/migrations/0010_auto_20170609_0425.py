# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('get_started', '0009_getstartedresponse_sent_emails'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='getstartedresponse',
            options={'default_permissions': ('add', 'change', 'export', 'delete')},
        ),
        migrations.AlterModelOptions(
            name='referralvoucher',
            options={'default_permissions': ('add', 'change', 'export', 'delete')},
        ),
    ]
