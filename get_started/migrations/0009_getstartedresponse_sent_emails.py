# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('get_started', '0008_emails48'),
    ]

    operations = [
        migrations.AddField(
            model_name='getstartedresponse',
            name='sent_emails',
            field=models.TextField(default='[]', max_length=192, null=True, blank=True),
        ),
    ]
