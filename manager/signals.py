# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models.signals import post_save
from django.dispatch import receiver

from manager.models import IntercomLocal

from metrics.tasks import send_metric


@receiver(post_save, sender=IntercomLocal)
def event_post_save(sender, instance, created, **kwargs):
    send_metric.delay('events', customer_id=instance.customer.id)
