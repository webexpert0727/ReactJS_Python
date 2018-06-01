# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_countries.fields
import django_hstore.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BrewMethod',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=32, verbose_name=b'Brew method')),
                ('img', models.ImageField(upload_to=b'')),
            ],
        ),
        migrations.CreateModel(
            name='CoffeeType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name=b'Coffee name')),
                ('maker', models.CharField(max_length=128, verbose_name=b'Coffee producer')),
                ('region', models.CharField(max_length=64, verbose_name=b'Region')),
                ('country', django_countries.fields.CountryField(max_length=2)),
                ('taste', models.CharField(max_length=128, verbose_name=b'Coffee taste')),
                ('more_taste', models.CharField(max_length=256, verbose_name=b'More taste')),
                ('body', models.IntegerField(verbose_name=b'Roast', choices=[(1, b'Light Roast'), (2, b'Light-Medium Roast'), (3, b'Medium Roast'), (4, b'Medium-Dark Roast'), (5, b'Dark Roast')])),
                ('roasted_on', models.DateField(default=None, null=True, verbose_name=b'Roasted on', blank=True)),
                ('shipping_till', models.DateField(default=None, null=True, verbose_name=b'Shipping untill', blank=True)),
                ('amount', models.DecimalField(default=18, verbose_name=b'Amount', max_digits=6, decimal_places=2)),
                ('profile', django_hstore.fields.DictionaryField(default={})),
                ('img', models.ImageField(upload_to=b'')),
                ('description', models.CharField(default=b'This coffee is good', max_length=2048, verbose_name=b'Description')),
                ('altitude', models.CharField(default=b'1256m', max_length=32)),
                ('varietal', models.CharField(default=b'Arabica', max_length=64)),
                ('process', models.CharField(default=b'Natural', max_length=32)),
                ('brew_method', models.ManyToManyField(to='coffees.BrewMethod')),
            ],
        ),
        migrations.CreateModel(
            name='Flavor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=32, verbose_name=b'Flavor')),
                ('img', models.ImageField(upload_to=b'')),
            ],
        ),
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.CharField(max_length=256, verbose_name=b'Header text')),
                ('active', models.BooleanField(default=True, verbose_name=b'Is active')),
            ],
        ),
    ]
