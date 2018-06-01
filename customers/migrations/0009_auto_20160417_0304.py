# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_hstore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0005_coffeegear'),
        ('customers', '0008_customer_amount'),
    ]

    operations = [
        migrations.CreateModel(
            name='GearOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name=b'Order time')),
                ('shipping_date', models.DateTimeField()),
                ('price', models.DecimalField(max_digits=6, decimal_places=2)),
                ('status', models.CharField(default=b'AC', max_length=16, choices=[(b'AC', b'Active'), (b'SH', b'Shipped'), (b'PA', b'Paused'), (b'CA', b'Canceled'), (b'ER', b'Failed'), (b'DE', b'Declined')])),
                ('details', django_hstore.fields.DictionaryField(default={}, blank=True)),
                ('customer', models.ForeignKey(to='customers.Customer')),
                ('gear', models.ForeignKey(to='coffees.CoffeeGear')),
            ],
        ),
        migrations.AddField(
            model_name='voucher',
            name='discount2',
            field=models.IntegerField(default=0, help_text=b'dollars', verbose_name=b'Discount ($)'),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='discount',
            field=models.IntegerField(default=0, help_text=b'percents', verbose_name=b'Discount (%)'),
        ),
    ]
