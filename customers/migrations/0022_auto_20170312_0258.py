# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0018_auto_20170312_0258'),
        ('customers', '0021_customer_extra'),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='Address name')),
                ('recipient_name', models.CharField(max_length=255, verbose_name='Full name of recipient')),
                ('country', django_countries.fields.CountryField(max_length=2)),
                ('line1', models.CharField(max_length=255, verbose_name='First line of address')),
                ('line2', models.CharField(max_length=255, verbose_name='Second line of address', blank=True)),
                ('postcode', models.CharField(max_length=13, verbose_name='Postal code')),
                ('is_primary', models.BooleanField(default=False, verbose_name='Primary address')),
                ('customer', models.ForeignKey(related_query_name='address', related_name='addresses', to='customers.Customer')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='CoffeeReview',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rating', models.IntegerField(null=True, blank=True)),
                ('comment', models.TextField(max_length=1024, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('coffee', models.ForeignKey(related_name='reviews', to='coffees.CoffeeType')),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
        migrations.RemoveField(
            model_name='emailspause',
            name='order',
        ),
        migrations.AlterModelOptions(
            name='gearorder',
            options={'ordering': ['-shipping_date']},
        ),
        migrations.AlterModelOptions(
            name='order',
            options={'ordering': ['-shipping_date']},
        ),
        migrations.AlterField(
            model_name='gearorder',
            name='customer',
            field=models.ForeignKey(related_name='gearorders', to='customers.Customer'),
        ),
        migrations.AlterField(
            model_name='gearorder',
            name='date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Creation Date'),
        ),
        migrations.AlterField(
            model_name='gearorder',
            name='shipping_date',
            field=models.DateTimeField(null=True, verbose_name='Shipping date', blank=True),
        ),
        migrations.AlterField(
            model_name='gearorder',
            name='status',
            field=models.CharField(default='AC', max_length=16, verbose_name='Status', choices=[('AC', 'Active'), ('SH', 'Shipped'), ('PA', 'Paused'), ('CA', 'Canceled'), ('ER', 'Failed'), ('DE', 'Declined')]),
        ),
        migrations.AlterField(
            model_name='order',
            name='customer',
            field=models.ForeignKey(related_name='orders', to='customers.Customer'),
        ),
        migrations.DeleteModel(
            name='EmailsPause',
        ),
        migrations.AddField(
            model_name='coffeereview',
            name='order',
            field=models.OneToOneField(related_name='review', to='customers.Order'),
        ),
        migrations.AddField(
            model_name='gearorder',
            name='address',
            field=models.ForeignKey(related_name='gearorders', blank=True, to='customers.Address', null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='address',
            field=models.ForeignKey(related_name='orders', blank=True, to='customers.Address', null=True),
        ),
    ]
