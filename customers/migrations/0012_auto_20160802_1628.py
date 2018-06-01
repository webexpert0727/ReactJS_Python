# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0011_auto_20160530_0208'),
    ]

    operations = [
        migrations.CreateModel(
            name='VoucherCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name_plural': 'Voucher categories',
            },
        ),
        migrations.AddField(
            model_name='voucher',
            name='category',
            field=models.ForeignKey(blank=True, to='customers.VoucherCategory', null=True),
        ),
    ]
