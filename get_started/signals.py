# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models.signals import post_save
from django.dispatch import receiver

from customers.tasks import mailchimp_subscribe

from metrics.tasks import send_metric

from .models import ReferralVoucher


@receiver(post_save, sender=ReferralVoucher)
def referral_voucher_post_save(sender, instance, created, **kwargs):
    if created:
        mailchimp_subscribe.delay(email=instance.recipient_email)
    send_metric.delay('invites', invite_id=instance.id)
