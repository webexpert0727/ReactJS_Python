# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0017_coffeegear_available'),
    ]

    operations = [
        migrations.CreateModel(
            name='FarmPhotos',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('photo1', models.ImageField(upload_to=b'', blank=True)),
                ('photo2', models.ImageField(upload_to=b'', blank=True)),
                ('photo3', models.ImageField(upload_to=b'', blank=True)),
                ('photo4', models.ImageField(upload_to=b'', blank=True)),
                ('photo5', models.ImageField(upload_to=b'', blank=True)),
            ],
        ),
        migrations.AlterModelOptions(
            name='coffeetype',
            options={'ordering': ['-id']},
        ),
        migrations.AddField(
            model_name='brewmethod',
            name='slug',
            field=models.SlugField(max_length=20, blank=True),
        ),
        migrations.AddField(
            model_name='coffeegear',
            name='brew_methods',
            field=models.ManyToManyField(to='coffees.BrewMethod'),
        ),
        migrations.AddField(
            model_name='coffeegear',
            name='recommend',
            field=models.BooleanField(default=False, verbose_name='Recommend'),
        ),
        migrations.AddField(
            model_name='coffeetype',
            name='acidity',
            field=models.CharField(default='Medium', max_length=16, verbose_name='Acidity'),
        ),
        migrations.AddField(
            model_name='farmphotos',
            name='coffee',
            field=models.ForeignKey(to='coffees.CoffeeType'),
        ),
    ]
