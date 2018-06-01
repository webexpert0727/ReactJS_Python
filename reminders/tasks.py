# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json
import logging
import requests
import urllib
from requests.auth import HTTPBasicAuth

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

from customers.models import Order

from celery.schedules import crontab
from celery.task import periodic_task

from djrill import MandrillRecipientsRefused

from get_started.models import GetStartedResponse

from giveback_project.settings import base

from .models import Reminder, ReminderSkipDelivery, ReminderSMS


logger = logging.getLogger('giveback_project.' + __name__)

burstsms_auth = HTTPBasicAuth(base.BURSTSMS_API_KEY, base.BURSTSMS_API_SECRET)

REACTIVATION_TEMPLATES = settings.REACTIVATION_TEMPLATES

@periodic_task(run_every=(crontab(minute="*/1")))
def send_reminders():
    ctz = timezone.get_current_timezone()
    now = ctz.normalize(timezone.now())

    reminders = (
        Reminder.objects
        .filter(completed=False, scheduled__lte=now)
        .exclude(order__status='CA'))

    reminders_skip = (
        ReminderSkipDelivery.objects
        .filter(completed=False, scheduled__lte=now)
        .exclude(order__status='CA'))

    reminders_sms = ReminderSMS.objects.filter(
        sent=False,
        scheduled__lte=now
        )

    for reminder in reminders:
        _send_reminder(reminder)

    for reminder in reminders_skip:
        _send_reminder(reminder)

    for reminder in reminders_sms:
        _send_sms(reminder)


def _send_reminder(reminder):
    try:
        to_email = reminder.email
        msg = EmailMessage(
            subject=reminder.subject,
            to=[to_email],
            from_email=reminder.from_email,
        )
        msg.template_name = reminder.template_name
        msg.merge_vars = {
            to_email: reminder.get_vars(),
        }
        msg.send()
    except MandrillRecipientsRefused:
        logger.error('Send reminder to %s', to_email, exc_info=True)
    except Exception:
        logger.error('Send reminder to %s', to_email, exc_info=True)
        return
    reminder.completed = True
    reminder.save()
    logger.debug('Reminder [%d] for <%s> sent successfully!' % (
        reminder.id, to_email))

    if reminder.template_name in REACTIVATION_TEMPLATES:
        try:
            gs_response = GetStartedResponse.objects.filter(email=to_email).latest("created")
            sent_emails = json.loads(gs_response.sent_emails)
            sent_emails.append(reminder.template_name)
            gs_response.sent_emails = json.dumps(sent_emails)
            gs_response.save()
        except (GetStartedResponse.DoesNotExist, Exception):
            logger.error('Updating gs_response for email: %s',
                         to_email, exc_info=True)


def _send_sms(sms_obj):
    if sms_obj.order.status == Order.SHIPPED:
        r = requests.post("https://api.transmitsms.com/send-sms.json",
            auth=burstsms_auth,
            data = {
                "message": "Hey %s\n\nSam from Hook Coffee here.\nJust wanted to check in to see if you have received your first bag of coffee and all is good with it!\nAnd if there is anything you need help with, please feel free to drop us a note or call back on this number.\nWe will be more than happy to help!\n\nBest,\nSam\n\nHook Coffee" % sms_obj.customer.first_name.title(),
                "to": sms_obj.number,
                "from": ReminderSMS.FROM_NUMBER,
            })

        response = r.json()
        if response and response.get("error"):
            sms_obj.sent = True
            if response.get("error").get("code") == "SUCCESS":
                logger.info("Sent sms to number {} <{}> on {}, cost - ${}".format(
                    sms_obj.number,
                    sms_obj.customer.user.email,
                    response.get("send_at"),
                    response.get("cost"),
                    )
                )
            else:
                code = response.get("error").get("code")
                description = response.get("error").get("description")
                sms_obj.error = "code: {}, desc: {}".format(code, description)
                logger.error("Failed sms to number {} <{}> on {}, code: {}, description: {}".format(
                    sms_obj.number,
                    sms_obj.customer.user.email,
                    timezone.now().date(),
                    code,
                    description,
                    )
                )
            sms_obj.save()

            return response

    return None
