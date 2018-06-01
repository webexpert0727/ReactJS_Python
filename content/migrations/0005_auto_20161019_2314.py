# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0004_career'),
    ]

    operations = [
        migrations.AddField(
            model_name='career',
            name='description_en',
            field=models.CharField(max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='career',
            name='description_zh_hans',
            field=models.CharField(max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='career',
            name='title_en',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='career',
            name='title_zh_hans',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='message_en',
            field=models.CharField(max_length=1536, null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='message_zh_hans',
            field=models.CharField(max_length=1536, null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='title_en',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='title_zh_hans',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='review',
            name='author_en',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='review',
            name='author_zh_hans',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='review',
            name='message_en',
            field=models.CharField(max_length=1536, null=True),
        ),
        migrations.AddField(
            model_name='review',
            name='message_zh_hans',
            field=models.CharField(max_length=1536, null=True),
        ),
        migrations.AddField(
            model_name='section',
            name='name_en',
            field=models.CharField(max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='section',
            name='name_zh_hans',
            field=models.CharField(max_length=32, null=True),
        ),
    ]
