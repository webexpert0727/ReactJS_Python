# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('customers', '0012_auto_20160802_1628'),
    ]

    operations = [
        migrations.CreateModel(
            name='FacebookCustomer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('facebook_id', models.CharField(max_length=255, verbose_name=b'Facebook ID')),
                ('first_name', models.CharField(max_length=255, verbose_name=b'First name')),
                ('last_name', models.CharField(max_length=255, verbose_name=b'Last name')),
                ('email', models.EmailField(unique=True, max_length=255, verbose_name=b'Email address')),
                ('gender', models.CharField(max_length=255, verbose_name=b'Gender')),
                ('customer', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
    ]
