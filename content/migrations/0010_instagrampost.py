# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_hstore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0009_greeting'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstagramPost',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(max_length=256)),
                ('data', django_hstore.fields.SerializedDictionaryField(editable=False, blank=True)),
            ],
        ),
    ]
