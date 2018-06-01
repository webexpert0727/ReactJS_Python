# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0010_voucher_mode'),
        ('get_started', '0006_podsearlybird'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReferralVoucher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('used', models.BooleanField(default=False)),
                ('recipient_email', models.CharField(max_length=64)),
                ('discount_percent', models.IntegerField(default=0, help_text=b'percents', verbose_name=b'Discount (%)')),
                ('discount_sgd', models.IntegerField(default=0, help_text=b'dollars', verbose_name=b'Discount ($)')),
                ('code', models.CharField(max_length=32)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('sender', models.ForeignKey(to='customers.Customer')),
            ],
        ),
    ]
