# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0028_vouchercategory_desc'),
    ]

    operations = [
        migrations.CreateModel(
            name='Postcard',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('customer_postcard', models.FileField(upload_to='postcards/')),
            ],
        ),
    ]
