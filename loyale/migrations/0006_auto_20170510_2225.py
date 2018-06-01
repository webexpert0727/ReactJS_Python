# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('loyale', '0005_auto_20170312_0258'),
    ]

    operations = [
        migrations.AlterField(
            model_name='redemitem',
            name='user',
            field=models.ForeignKey(related_name='redems', to=settings.AUTH_USER_MODEL),
        ),
    ]
