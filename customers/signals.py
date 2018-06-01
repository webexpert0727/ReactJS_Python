# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import re
import stripe

from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from customers.models import Customer, GearOrder, Order, Plan, ShoppingCart
from customers.tasks import (
    add_event, create_intercom_profile, mailchimp_segment_member_del,
    mailchimp_subscribe, stripe_get_card_fingerprint, update_intercom_profile)

from giveback_project.settings import base

from metrics.tasks import send_metric


@receiver(pre_delete, sender=Plan)
def delete_delete(instance, **kwargs):

    print 'Deleting plan "{}"'.format(str(instance))

    stripe.api_key = base.SECRET_KEY

    try:
    	current_plan = stripe.Plan.retrieve(instance.plan)
    	current_plan.delete()
    except:
    	'Error while deleting plan "{}"'.format(str(instance))


@receiver(user_logged_in)
def logged_in(sender, request, user, **kwargs):
    # FIXME: How and why an user haven't relation to customer?
    try:
        customer_id = user.customer.id
    except Customer.DoesNotExist:
        pass
    else:
        add_event.delay(customer_id=customer_id, event='logged-in')

        try:
            cart = ShoppingCart.objects.get(customer=user.customer)
            request.session['shopping-cart'] = json.loads(cart.content)
        except ShoppingCart.DoesNotExist:
            pass


@receiver(user_logged_out)
def logged_out(sender, request, user, **kwargs):
    # FIXME: How and why an user haven't relation to customer?
    if user:
        try:
            customer_id = user.customer.id
        except Customer.DoesNotExist:
            pass
        else:
            add_event.delay(customer_id=customer_id, event='logged-out')


@receiver(post_save, sender=GearOrder)
def gear_order_post_save(sender, instance, created, **kwargs):
    update_intercom_profile.delay(customer_id=instance.customer.id)
    send_metric.delay('gear_orders', order_id=instance.id)
    send_metric.delay('customers', customer_id=instance.customer.id)


@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    update_intercom_profile.delay(customer_id=instance.customer.id)
    send_metric.delay('orders', order_id=instance.id)
    send_metric.delay('customers', customer_id=instance.customer.id)


@receiver(post_save, sender=Customer)
def customer_post_save(sender, instance, created, **kwargs):
    if created:
        stripe_get_card_fingerprint.delay(
            customer_id=instance.id,
            cus_stripe_id=instance.stripe_id)
        leads_segment_id = settings.MAILCHIMP_LEADS_SEGMENT
        mailchimp_subscribe.delay(
            email=instance.user.email,
            is_lead=False,
            merge_vars={'FNAME': instance.first_name,
                        'LNAME': instance.last_name})
        mailchimp_segment_member_del.apply_async(
            (instance.user.email, leads_segment_id),
            countdown=20)
        create_intercom_profile.delay(email=instance.user.email)
        update_intercom_profile.apply_async((instance.id, ), countdown=3)
    else:
        update_intercom_profile.delay(customer_id=instance.id)
    send_metric.delay('customers', customer_id=instance.id)

@receiver(pre_save, sender=Customer)
def customer_pre_save(sender, instance, **kwargs):
    phone = instance.phone
    if phone:
        if phone[0] != "+" and (phone[:2] != "65" or len(phone) <= 8):
            phone = "65" + phone
        instance.phone = re.sub(r"[ +]", "", phone)
