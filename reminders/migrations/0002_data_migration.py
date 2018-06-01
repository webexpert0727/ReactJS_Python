# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta

from django.db import models, migrations


def add_existing_data(apps, schema_editor):
    Reminder = apps.get_model("reminders", "Reminder")

    Emails24 = apps.get_model("get_started", "Emails24")
    for email24 in Emails24.objects.all():
        Reminder.objects.create(
            username=email24.username,
            email=email24.email,
            from_email='Hook Coffee <hola@hookcoffee.com.sg>',
            subject='We see that you’ve signed up but haven’t ordered',
            template_name='We see that you’ve signed up but haven’t ordered',
            scheduled=email24.time + timedelta(hours=4),
        )
    print 'Emails24:', 'OK'

    Emails48 = apps.get_model("get_started", "Emails48")
    for email48 in Emails48.objects.all():
        Reminder.objects.create(
            username=email48.username,
            email=email48.email,
            from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
            subject='Still considering?',
            template_name='Re-engagement from Faye',
            scheduled=email48.time + timedelta(hours=24),
        )
    print 'Emails48:', 'OK'

    Emails7 = apps.get_model("get_started", "Emails7")
    for email7 in Emails7.objects.all():
        Reminder.objects.create(
            username=email7.username,
            email=email7.email,
            from_email='Hook Coffee <hola@hookcoffee.com.sg>',
            subject='Which was your favourite?',
            template_name='Which was your favourite?',
            scheduled=email7.time + timedelta(days=7),
        )
    print 'Emails7:', 'OK'

    EmailsPause = apps.get_model("customers", "EmailsPause")
    for emailPause in EmailsPause.objects.all():
        if emailPause.order.status != 'PA':
            continue
        # print 'emailPause.order:', emailPause.order, 'emailPause.order.shipping_date:', emailPause.order.shipping_date
        Reminder.objects.create(
            username=emailPause.order.customer.first_name,
            email=emailPause.order.customer.user.email,
            order=emailPause.order,
            from_email='Hook Coffee <hola@hookcoffee.com.sg>',
            subject='Welcome back! Your paused subscription is to be resumed.',
            template_name='Paused subscription to be resumed',
            resumed=emailPause.order.shipping_date,
            scheduled=emailPause.order.shipping_date - timedelta(days=3),
        )
    print 'EmailsPause:', 'OK'


def remove_all_data(apps, schema_editor):
    Reminder = apps.get_model("reminders", "Reminder")
    print 'objects:', Reminder.objects.all().count()
    print 'objects deleted:', Reminder.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('reminders', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_existing_data, remove_all_data),

    ]
