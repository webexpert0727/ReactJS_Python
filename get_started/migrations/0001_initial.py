# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_hstore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GetStartedResponse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=32, verbose_name=b'Username')),
                ('email', models.EmailField(max_length=254, verbose_name=b'Email address')),
                ('form_details', django_hstore.fields.DictionaryField(default={})),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('ct', models.ForeignKey(blank=True, to='coffees.CoffeeType', null=True)),
            ],
        ),
    ]
