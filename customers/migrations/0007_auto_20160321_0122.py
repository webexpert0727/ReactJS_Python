# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_hstore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0006_order_details'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailsPause',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resume_time', models.DateTimeField()),
            ],
        ),
        migrations.AlterField(
            model_name='order',
            name='details',
            field=django_hstore.fields.DictionaryField(default={}, blank=True),
        ),
        migrations.AddField(
            model_name='emailspause',
            name='order',
            field=models.OneToOneField(to='customers.Order'),
        ),
    ]
