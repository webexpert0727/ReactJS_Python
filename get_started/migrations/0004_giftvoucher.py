# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0008_customer_amount'),
        ('get_started', '0003_emails7'),
    ]

    operations = [
        migrations.CreateModel(
            name='GiftVoucher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('used', models.BooleanField(default=False)),
                ('recipient', models.CharField(max_length=64)),
                ('amount', models.IntegerField(default=18, help_text=b'SGD', verbose_name=b'Credits')),
                ('code', models.CharField(max_length=32)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('sender', models.ForeignKey(to='customers.Customer')),
            ],
        ),
    ]
