# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coffees', '0005_coffeegear'),
    ]

    operations = [
        migrations.CreateModel(
            name='CoffeeSticker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=b'Hook Coffee Singapore', max_length=256, verbose_name=b'Name', blank=True)),
                ('description', models.CharField(
                    default=(b'We deliver specialty coffee, sourced from the world\'s best farms '
                             b'and hand-roasted locally in Singapore. Your fresh and delicious '
                             b'coffee is sent out to you within a week of roasting, just the way '
                             b'you want it, and straight to your mailbox! #IAMHOOKED'),
                    max_length=256, verbose_name=b'Description', blank=True)),
                ('caption', models.CharField(default=b'HOOKCOFFEE.COM.SG', max_length=256, verbose_name=b'Caption', blank=True)),
                ('hashtag', models.CharField(default=b'#HOOKCOFFEESG', max_length=256, verbose_name=b'Hashtag', blank=True)),
                ('sticker', models.FileField(default='stickers/sweet_bundchen_1024.png', upload_to=b'stickers/')),
                ('coffee', models.ForeignKey(to='coffees.CoffeeType')),
            ],
        ),
    ]

