# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wholesale', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='comments_en',
            field=models.CharField(max_length=256, null=True, verbose_name=b'Comments'),
        ),
        migrations.AddField(
            model_name='plan',
            name='comments_zh_hans',
            field=models.CharField(max_length=256, null=True, verbose_name=b'Comments'),
        ),
        migrations.AddField(
            model_name='plan',
            name='description_1_en',
            field=models.CharField(max_length=128, null=True, verbose_name=b'Description 1'),
        ),
        migrations.AddField(
            model_name='plan',
            name='description_1_zh_hans',
            field=models.CharField(max_length=128, null=True, verbose_name=b'Description 1'),
        ),
        migrations.AddField(
            model_name='plan',
            name='description_2_en',
            field=models.CharField(max_length=128, null=True, verbose_name=b'Description 2'),
        ),
        migrations.AddField(
            model_name='plan',
            name='description_2_note_en',
            field=models.CharField(default=None, max_length=128, null=True, verbose_name=b'Description 2 note', blank=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='description_2_note_zh_hans',
            field=models.CharField(default=None, max_length=128, null=True, verbose_name=b'Description 2 note', blank=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='description_2_zh_hans',
            field=models.CharField(max_length=128, null=True, verbose_name=b'Description 2'),
        ),
        migrations.AddField(
            model_name='plan',
            name='goal_1_en',
            field=models.CharField(max_length=128, null=True, verbose_name=b'Goal 1'),
        ),
        migrations.AddField(
            model_name='plan',
            name='goal_1_zh_hans',
            field=models.CharField(max_length=128, null=True, verbose_name=b'Goal 1'),
        ),
        migrations.AddField(
            model_name='plan',
            name='goal_2_en',
            field=models.CharField(max_length=128, null=True, verbose_name=b'Goal 2'),
        ),
        migrations.AddField(
            model_name='plan',
            name='goal_2_note_en',
            field=models.CharField(default=None, max_length=128, null=True, verbose_name=b'Goal 2 note', blank=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='goal_2_note_zh_hans',
            field=models.CharField(default=None, max_length=128, null=True, verbose_name=b'Goal 2 note', blank=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='goal_2_zh_hans',
            field=models.CharField(max_length=128, null=True, verbose_name=b'Goal 2'),
        ),
        migrations.AddField(
            model_name='plan',
            name='name_en',
            field=models.CharField(max_length=64, null=True, verbose_name=b'Title'),
        ),
        migrations.AddField(
            model_name='plan',
            name='name_zh_hans',
            field=models.CharField(max_length=64, null=True, verbose_name=b'Title'),
        ),
    ]
