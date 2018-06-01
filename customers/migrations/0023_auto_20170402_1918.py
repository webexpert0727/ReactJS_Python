# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0022_auto_20170312_0258'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShoppingCart',
            fields=[
                ('customer', models.OneToOneField(related_name='shopping_cart', primary_key=True, serialize=False, to='customers.Customer')),
                ('content', models.TextField(max_length=1024)),
                ('last_modified', models.DateTimeField()),
                ('first_reminder', models.BooleanField(default=False)),
                ('second_reminder', models.BooleanField(default=False)),
            ],
        ),
        migrations.AlterField(
            model_name='voucher',
            name='category',
            field=models.ForeignKey(default=1, to='customers.VoucherCategory'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='shoppingcart',
            name='voucher',
            field=models.OneToOneField(null=True, blank=True, to='customers.Voucher'),
        ),
    ]
