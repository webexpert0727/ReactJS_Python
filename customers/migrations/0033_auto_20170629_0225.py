# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0032_cardfingerprint'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='coffeereview',
            options={'ordering': ['-id'], 'default_permissions': ('add', 'change', 'export', 'delete')},
        ),
    ]
