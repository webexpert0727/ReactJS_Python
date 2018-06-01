# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings
import django.core.validators
import django_hstore.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('coffees', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Charge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.CharField(max_length=32, blank=True)),
                ('description', models.CharField(max_length=255, blank=True)),
                ('metadata', django_hstore.fields.DictionaryField(default={}, verbose_name=b'Metadata', blank=True)),
                ('date', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('stripe_id', models.CharField(max_length=255, verbose_name=b'Stripe charge ID', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=255, verbose_name=b'First name')),
                ('last_name', models.CharField(max_length=255, verbose_name=b'Last name')),
                ('line1', models.CharField(max_length=255, verbose_name=b'First line of address')),
                ('line2', models.CharField(max_length=255, verbose_name=b'Second line of address', blank=True)),
                ('postcode', models.CharField(max_length=10, verbose_name=b'Postal code', validators=[django.core.validators.RegexValidator(b'^\\d{6}$')])),
                ('stripe_id', models.CharField(max_length=255, verbose_name=b'Stripe customer ID', blank=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('different', models.BooleanField(default=False, verbose_name=b'Different?')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name=b'Creation Date')),
                ('shipping_date', models.DateTimeField(null=True, verbose_name=b'Shipping date', blank=True)),
                ('amount', models.DecimalField(default=18, verbose_name=b'Amount', max_digits=6, decimal_places=2)),
                ('interval', models.PositiveIntegerField(default=7, verbose_name=b'Shipping Interval')),
                ('recurrent', models.BooleanField(default=False, verbose_name=b'Recurrent?')),
                ('status', models.CharField(default=b'AC', max_length=16, verbose_name=b'Status', choices=[(b'AC', b'Active'), (b'SH', b'Shipped'), (b'PA', b'Paused'), (b'CA', b'Canceled'), (b'ER', b'Failed')])),
                ('package', models.CharField(default=b'GR', max_length=16, verbose_name=b'Packaging method', choices=[(b'GR', b'Grounded'), (b'WB', b'Wholebeans'), (b'DR', b'Drip bags')])),
                ('brew', models.ForeignKey(blank=True, to='coffees.BrewMethod', null=True)),
                ('coffee', models.ForeignKey(to='coffees.CoffeeType')),
                ('customer', models.ForeignKey(to='customers.Customer')),
            ],
        ),
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('plan', models.CharField(unique=True, max_length=32, verbose_name=b'Plan ID')),
                ('name', models.CharField(max_length=255, blank=True)),
                ('currency', models.CharField(default=b'SGD', max_length=4, blank=True)),
                ('amount', models.IntegerField(help_text=b'in cent')),
                ('metadata', django_hstore.fields.DictionaryField(default={}, blank=True)),
                ('interval', models.CharField(default=b'week', max_length=16, choices=[(b'day', b'day'), (b'week', b'week'), (b'month', b'month'), (b'year', b'year')])),
                ('interval_count', models.IntegerField(default=1)),
                ('stripe_id', models.CharField(verbose_name=b'Stripe plan ID', max_length=64, editable=False, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Preferences',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('package', models.CharField(default=b'GR', max_length=16, verbose_name=b'Packaging method', choices=[(b'GR', b'Grounded'), (b'WB', b'Wholebeans'), (b'DR', b'Drip bags')])),
                ('decaf', models.BooleanField(default=False, verbose_name=b'Decaffeinated?')),
                ('different', models.BooleanField(default=False, verbose_name=b'Different?')),
                ('cups', models.PositiveIntegerField(default=7, verbose_name=b'Cups per week')),
                ('intense', models.PositiveIntegerField(default=5, verbose_name=b'Intense')),
                ('interval', models.PositiveIntegerField(default=7, verbose_name=b'Shipping Interval')),
                ('force_coffee', models.BooleanField(default=False, verbose_name=b'Force sending coffee choosen by client')),
                ('brew', models.ForeignKey(blank=True, to='coffees.BrewMethod', null=True)),
                ('coffee', models.ForeignKey(blank=True, to='coffees.CoffeeType', null=True)),
                ('customer', models.OneToOneField(to='customers.Customer')),
                ('flavor', models.ManyToManyField(to='coffees.Flavor', blank=True)),
            ],
            options={
                'verbose_name_plural': 'Preferences',
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('metadata', django_hstore.fields.DictionaryField(default={}, blank=True)),
                ('stripe_id', models.CharField(verbose_name=b'Stripe subscription ID', max_length=255, editable=False, blank=True)),
                ('status', models.CharField(default=b'active', max_length=b'32', choices=[(b'active', b'active'), (b'paused', b'paused')])),
                ('customer', models.ForeignKey(to='customers.Customer')),
                ('plan', models.ForeignKey(to='customers.Plan')),
            ],
        ),
        migrations.CreateModel(
            name='Voucher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=b'TRYUS50', max_length=32)),
                ('discount', models.IntegerField(default=50, help_text=b'percents')),
                ('count', models.PositiveSmallIntegerField(default=0, verbose_name=b'Times used')),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='voucher',
            field=models.ForeignKey(blank=True, to='customers.Voucher', null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='vouchers',
            field=models.ManyToManyField(to='customers.Voucher', blank=True),
        ),
        migrations.AddField(
            model_name='charge',
            name='customer',
            field=models.ForeignKey(to='customers.Customer'),
        ),
        migrations.AddField(
            model_name='charge',
            name='product',
            field=models.ForeignKey(to='coffees.CoffeeType'),
        ),
    ]
