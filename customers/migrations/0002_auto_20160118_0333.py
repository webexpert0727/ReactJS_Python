# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('referred', models.ForeignKey(related_name='Referrer', to=settings.AUTH_USER_MODEL)),
                ('referrer', models.ForeignKey(related_name='Referred', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Referral',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('aim', models.CharField(default=b'GE', max_length=16, choices=[(b'GE', b'General'), (b'FB', b'Facebook')])),
                ('code', models.CharField(max_length=64, null=True, blank=True)),
                ('status', models.CharField(default=b'AC', max_length=16, choices=[(b'AC', b'Active'), (b'NA', b'Inactive')])),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='preferences',
            name='present_next',
            field=models.BooleanField(default=False, verbose_name=b'Make next order free'),
        ),
        migrations.AlterField(
            model_name='order',
            name='brew',
            field=models.ForeignKey(to='coffees.BrewMethod'),
        ),
        migrations.AlterField(
            model_name='order',
            name='package',
            field=models.CharField(default=b'GR', max_length=16, verbose_name=b'Packaging method', choices=[(b'GR', b'Grounded (250g)'), (b'WB', b'Wholebeans (250g)'), (b'DR', b'Drip bags (x10)')]),
        ),
        migrations.AlterField(
            model_name='preferences',
            name='package',
            field=models.CharField(default=b'GR', max_length=16, verbose_name=b'Packaging method', choices=[(b'GR', b'Grounded (250g)'), (b'WB', b'Wholebeans (250g)'), (b'DR', b'Drip bags (x10)')]),
        ),
        migrations.AlterUniqueTogether(
            name='referral',
            unique_together=set([('user', 'aim')]),
        ),
        migrations.AlterUniqueTogether(
            name='reference',
            unique_together=set([('referrer', 'referred')]),
        ),
    ]
