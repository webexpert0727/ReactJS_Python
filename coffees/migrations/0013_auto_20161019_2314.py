# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0012_rawbean_created_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='CoffeeGearColor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30, verbose_name='Color name')),
            ],
        ),
        migrations.CreateModel(
            name='CoffeeGearImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', models.ImageField(upload_to=b'')),
            ],
        ),
        migrations.RemoveField(
            model_name='coffeegear',
            name='img',
        ),
        migrations.AddField(
            model_name='brewmethod',
            name='name_en',
            field=models.CharField(max_length=32, null=True, verbose_name='Brew method'),
        ),
        migrations.AddField(
            model_name='brewmethod',
            name='name_zh_hans',
            field=models.CharField(max_length=32, null=True, verbose_name='Brew method'),
        ),
        migrations.AddField(
            model_name='coffeegear',
            name='description_en',
            field=models.CharField(max_length=512, null=True, verbose_name='Description', blank=True),
        ),
        migrations.AddField(
            model_name='coffeegear',
            name='description_zh_hans',
            field=models.CharField(max_length=512, null=True, verbose_name='Description', blank=True),
        ),
        migrations.AddField(
            model_name='coffeegear',
            name='in_stock',
            field=models.BooleanField(default=True, verbose_name='In Stock'),
        ),
        migrations.AddField(
            model_name='coffeegear',
            name='link_en',
            field=models.CharField(default='#', max_length=256, null=True, verbose_name='Watch brew guide link'),
        ),
        migrations.AddField(
            model_name='coffeegear',
            name='link_zh_hans',
            field=models.CharField(default='#', max_length=256, null=True, verbose_name='Watch brew guide link'),
        ),
        migrations.AddField(
            model_name='coffeegear',
            name='model_en',
            field=models.CharField(max_length=32, null=True, verbose_name='Model'),
        ),
        migrations.AddField(
            model_name='coffeegear',
            name='model_zh_hans',
            field=models.CharField(max_length=32, null=True, verbose_name='Model'),
        ),
        migrations.AddField(
            model_name='coffeegear',
            name='more_info',
            field=models.TextField(max_length=2048, verbose_name='More info', blank=True),
        ),
        migrations.AddField(
            model_name='coffeegear',
            name='more_info_en',
            field=models.TextField(max_length=2048, null=True, verbose_name='More info', blank=True),
        ),
        migrations.AddField(
            model_name='coffeegear',
            name='more_info_zh_hans',
            field=models.TextField(max_length=2048, null=True, verbose_name='More info', blank=True),
        ),
        migrations.AddField(
            model_name='coffeegear',
            name='name_en',
            field=models.CharField(max_length=64, null=True, verbose_name='Title'),
        ),
        migrations.AddField(
            model_name='coffeegear',
            name='name_zh_hans',
            field=models.CharField(max_length=64, null=True, verbose_name='Title'),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='altitude_en',
            field=models.CharField(default='1256m', max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='altitude_zh_hans',
            field=models.CharField(default='1256m', max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='description_en',
            field=models.CharField(default='This coffee is good', max_length=2048, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='description_zh_hans',
            field=models.CharField(default='This coffee is good', max_length=2048, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='maker_en',
            field=models.CharField(max_length=128, null=True, verbose_name='Coffee producer'),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='maker_zh_hans',
            field=models.CharField(max_length=128, null=True, verbose_name='Coffee producer'),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='more_taste_en',
            field=models.CharField(max_length=256, null=True, verbose_name='More taste'),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='more_taste_zh_hans',
            field=models.CharField(max_length=256, null=True, verbose_name='More taste'),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='process_en',
            field=models.CharField(default='Natural', max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='process_zh_hans',
            field=models.CharField(default='Natural', max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='region_en',
            field=models.CharField(max_length=64, null=True, verbose_name='Region'),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='region_zh_hans',
            field=models.CharField(max_length=64, null=True, verbose_name='Region'),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='taste_en',
            field=models.CharField(max_length=128, null=True, verbose_name='Coffee taste'),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='taste_zh_hans',
            field=models.CharField(max_length=128, null=True, verbose_name='Coffee taste'),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='varietal_en',
            field=models.CharField(default='Arabica', max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='varietal_zh_hans',
            field=models.CharField(default='Arabica', max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='flavor',
            name='name_en',
            field=models.CharField(max_length=32, null=True, verbose_name='Flavor'),
        ),
        migrations.AddField(
            model_name='flavor',
            name='name_zh_hans',
            field=models.CharField(max_length=32, null=True, verbose_name='Flavor'),
        ),
        migrations.AlterField(
            model_name='coffeegear',
            name='description',
            field=models.CharField(max_length=512, verbose_name='Description', blank=True),
        ),
        migrations.AddField(
            model_name='coffeegearimage',
            name='coffee_gear',
            field=models.ForeignKey(related_name='images', to='coffees.CoffeeGear'),
        ),
        migrations.AddField(
            model_name='coffeegearimage',
            name='color',
            field=models.ForeignKey(related_name='+', blank=True, to='coffees.CoffeeGearColor', null=True),
        ),
    ]
