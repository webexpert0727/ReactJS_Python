# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0015_order_resent'),
        ('coffees', '0011_rawbean'),
        ('manager', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChurnRateData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('month_year', models.CharField(max_length=255, verbose_name=b'Month and Year')),
                ('proportion_churned', models.DecimalField(default=0, verbose_name=b'Proportion Churned', max_digits=10, decimal_places=6)),
            ],
        ),
        migrations.CreateModel(
            name='MailchimpCampaignStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action', models.CharField(default=b'NA', max_length=16, verbose_name=b'Action', choices=[(b'NA', b'No Action'), (b'GS', b'Visited Get Started'), (b'PU', b'Purchased')])),
                ('email', models.CharField(max_length=255, verbose_name=b'email')),
                ('campaign_id', models.CharField(max_length=255, verbose_name=b'First name')),
                ('order', models.ForeignKey(default=None, blank=True, to='customers.Order', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='RawBeanStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name=b'Transaction Date')),
                ('buy_amount', models.DecimalField(default=Decimal('0.00'), verbose_name=b'Buy Amount', max_digits=6, decimal_places=2)),
                ('roasted_amount', models.DecimalField(default=Decimal('0.00'), verbose_name=b'Roasted Amount', max_digits=6, decimal_places=2)),
                ('remarks', models.CharField(max_length=512, null=True, verbose_name=b'Remarks')),
                ('raw_bean', models.ForeignKey(to='coffees.RawBean')),
            ],
        ),
    ]
