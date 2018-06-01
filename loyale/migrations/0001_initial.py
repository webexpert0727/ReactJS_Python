# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('coffees', '0005_coffeegear'),
    ]

    operations = [
        migrations.CreateModel(
            name='CoffeeTypePoints',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(blank=True, max_length=32, null=True, choices=[(b'subscribe', b'Subscribe'), (b'none', b'Not subscribe')])),
                ('points', models.IntegerField()),
                ('coffee_type', models.ForeignKey(to='coffees.CoffeeType')),
            ],
        ),
        migrations.CreateModel(
            name='GrantPointLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('points', models.IntegerField()),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, null=True, blank=True)),
                ('description', models.CharField(max_length=200, null=True, blank=True)),
                ('points', models.IntegerField(default=0)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('img', models.ImageField(upload_to=b'', blank=True)),
            ],
            options={
                'verbose_name': 'Redemption items',
                'verbose_name_plural': 'Redemption items',
            },
        ),
        migrations.CreateModel(
            name='OrderPoints',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sub_regular', models.IntegerField(default=200, help_text=b'Regular coffee subscription', verbose_name=b'Subsequent usual coffee')),
                ('sub_special', models.IntegerField(default=300, help_text=b'Special coffee subscription', verbose_name=b'Subsequent premium coffee')),
                ('one_regular', models.IntegerField(default=50, help_text=b'Regular coffee alacarte', verbose_name=b'One-off usual coffee')),
                ('one_special', models.IntegerField(default=75, help_text=b'Special coffee alacarte', verbose_name=b'One-off premium coffee')),
                ('credits', models.IntegerField(default=1, help_text=b'Benies amount for every gifted dollar', verbose_name=b'Gift credits')),
            ],
            options={
                'verbose_name': 'Settings',
                'verbose_name_plural': 'Settings',
            },
        ),
        migrations.CreateModel(
            name='Point',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('points', models.IntegerField()),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': "User's points",
                'verbose_name_plural': "User's points",
            },
        ),
        migrations.CreateModel(
            name='RedemItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(default=b'pending', max_length=32, choices=[(b'pending', b'Pending'), (b'done', b'Done')])),
                ('points', models.IntegerField(default=0)),
                ('shipping_date', models.DateTimeField(null=True, verbose_name=b'Shipping date', blank=True)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('item', models.ForeignKey(to='loyale.Item')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Orders',
                'verbose_name_plural': 'Orders',
            },
        ),
        migrations.CreateModel(
            name='RedemPointLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('points', models.IntegerField()),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('item', models.ForeignKey(to='loyale.Item')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SetPoint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(max_length=32, choices=[(b'subscribe', b'Subscribe'), (b'none', b'Not subscribe')])),
                ('points', models.IntegerField(default=0)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='setpoint',
            unique_together=set([('status', 'points')]),
        ),
    ]
