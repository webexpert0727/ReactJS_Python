# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wholesale', '0003_plan_office_type'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='plan',
            options={'ordering': ('the_order',)},
        ),
        migrations.AddField(
            model_name='plan',
            name='the_order',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AlterField(
            model_name='plan',
            name='description_2',
            field=models.CharField(max_length=128, null=True, verbose_name=b'Description 2', blank=True),
        ),
        migrations.AlterField(
            model_name='plan',
            name='description_2_en',
            field=models.CharField(max_length=128, null=True, verbose_name=b'Description 2', blank=True),
        ),
        migrations.AlterField(
            model_name='plan',
            name='description_2_zh_hans',
            field=models.CharField(max_length=128, null=True, verbose_name=b'Description 2', blank=True),
        ),
        migrations.AlterField(
            model_name='plan',
            name='goal_2',
            field=models.CharField(max_length=128, null=True, verbose_name=b'Goal 2', blank=True),
        ),
        migrations.AlterField(
            model_name='plan',
            name='goal_2_en',
            field=models.CharField(max_length=128, null=True, verbose_name=b'Goal 2', blank=True),
        ),
        migrations.AlterField(
            model_name='plan',
            name='goal_2_zh_hans',
            field=models.CharField(max_length=128, null=True, verbose_name=b'Goal 2', blank=True),
        ),
    ]
