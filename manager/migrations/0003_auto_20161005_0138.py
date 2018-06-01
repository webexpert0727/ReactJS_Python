# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0015_order_resent'),
        ('manager', '0002_churnratedata_mailchimpcampaignstats_rawbeanstats'),
    ]

    operations = [
        migrations.CreateModel(
            name='IntercomLocal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('event', models.CharField(max_length=255, verbose_name=b'event_name')),
                ('data', django_extensions.db.fields.json.JSONField()),
                ('added_timestamp', models.DateTimeField(auto_now_add=True, verbose_name=b'added')),
                ('customer', models.ForeignKey(to='customers.Customer')),
            ],
        ),
        migrations.RemoveField(
            model_name='rawbeanstats',
            name='buy_amount',
        ),
        migrations.RemoveField(
            model_name='rawbeanstats',
            name='remarks',
        ),
        migrations.RemoveField(
            model_name='rawbeanstats',
            name='roasted_amount',
        ),
        migrations.AddField(
            model_name='rawbeanstats',
            name='status',
            field=models.BooleanField(default=True, verbose_name=b'Available'),
        ),
        migrations.AddField(
            model_name='rawbeanstats',
            name='stock',
            field=models.DecimalField(default=Decimal('0.00'), verbose_name=b'Stock', max_digits=6, decimal_places=2),
        ),
    ]
