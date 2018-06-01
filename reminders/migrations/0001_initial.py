# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Reminder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(max_length=32)),
                ('email', models.EmailField(max_length=254)),
                ('from_email', models.CharField(default=b'Hook Coffee <hola@hookcoffee.com.sg>', max_length=100)),
                ('subject', models.CharField(max_length=100)),
                ('template_name', models.CharField(max_length=100)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('resumed', models.DateTimeField(null=True, blank=True)),
                ('scheduled', models.DateTimeField()),
                ('completed', models.BooleanField(default=False)),
                ('order', models.ForeignKey(blank=True, to='customers.Order', null=True)),
            ],
        ),
    ]
