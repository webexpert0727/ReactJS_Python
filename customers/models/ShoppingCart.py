# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from customers.models import Customer, Voucher, VoucherCategory
from django.utils import timezone

from django.core.mail import EmailMessage
from djrill import MandrillRecipientsRefused

import json
import logging
import random

from get_started.helpers import vouchers_allowed


logger = logging.getLogger(__name__)
PRICE_PREFIX = "S$"

class ShoppingCartManager(models.Manager):
    def empty(self):
        return self.model.objects.filter(content="[]")


class ShoppingCart(models.Model):
    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='shopping_cart'
        )
    content = models.TextField(max_length=1024)
    last_modified = models.DateTimeField()
    first_reminder = models.BooleanField(default=False)
    second_reminder = models.BooleanField(default=False)
    voucher = models.OneToOneField(Voucher, null=True, blank=True, on_delete=models.SET_NULL)

    objects = ShoppingCartManager()

    def save(self, *args, **kwargs):
        self.last_modified = timezone.now()
        super(self.__class__, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.voucher:
            self.disable_voucher()
        return super(self.__class__, self).delete(*args, **kwargs)

    def __unicode__(self):
        return "{}:{}".format(self.customer, self.last_modified.strftime('%HH:%MM'))

    def send_first_reminder(self):
        if self._send_reminder(
            "Re: Oops, You left something behind!",
            "Hook Coffee <hola@hookcoffee.com.sg>",
            "Re-engagement abandoned shopping cart 4hrs"):
            self.first_reminder = True
            self.save()

    def send_second_reminder(self):
        if not self.voucher:
            self.voucher = self._generate_voucher()

        # don't send if Christmas calendar is in cart
        forbidden = False
        cart = json.loads(self.content)
        for cart_item in cart:
            if not vouchers_allowed(cart_item):
                forbidden = True
                break

        if not forbidden:
            if self._send_reminder(
                "{}, still considering?".format(self.customer.first_name),
                "Hook Coffee <hola@hookcoffee.com.sg>",
                "Re-engagement abandoned shopping cart 24hrs",
                voucher=self.voucher.name):

                self.second_reminder = True
        else:
            logger.debug("Forbidden to send second reminder to {0}".format(self.customer))

        self.save()

    def _send_reminder(self, subject, from_email, template_name, voucher=None):
        try:
            to_email = self.customer.user.email
            msg = EmailMessage(
                subject=subject,
                to=[to_email],
                from_email=from_email,
            )
            msg.template_name = template_name
            msg.merge_vars = {
                to_email: self._get_merge_vars(voucher),
            }
            msg.send()
        except MandrillRecipientsRefused:
            logger.error('Send shopping cart reminder to %s',
                         to_email, exc_info=True)
        except Exception:
            logger.error('Send shopping cart reminder to %s',
                         to_email, exc_info=True)
            return False

        logger.debug('Shopping cart reminder for {} sent successfully!'.format(
            to_email))
        return True

    def _get_merge_vars(self, voucher):
        cart = json.loads(self.content)

        order_list = ""
        old_price = 0

        for i in cart:
            if i.get("coffee"):
                order_list += "{1} x {0}, ".format(i["coffee"]["name"], i["quantity"])
                old_price += float(i["coffee"]["price"]) * int(i["quantity"])
            elif i.get("gear"):
                order_list += "{1} x {0}, ".format(i["gear"]["name"], i["quantity"])
                old_price += float(i["gear"]["price"]) * int(i["quantity"])

        new_price = PRICE_PREFIX + str(old_price * 0.9)
        savings = PRICE_PREFIX + str(old_price * 0.1)

        old_price = PRICE_PREFIX + str(old_price)

        return {
            "USERNAME": self.customer.first_name,
            "ORDER_LIST": order_list[:-2],
            "OLD_PRICE": old_price,
            "NEW_PRICE": new_price,
            "SAVINGS": savings,
            "VOUCHER": voucher,
        }

    def _generate_voucher(self):
        name = "{}0{}{}".format(
            self.customer.first_name.replace(" ", "").upper(),
            "".join(random.sample("QWERTYUIOPASDFGHJKLZXCVBNM", 3)),
            "10"
            )
        voucher_cat = VoucherCategory.objects.get(name="shopping cart")
        voucher = Voucher.objects.create(
            name=name,
            discount=10,
            category=voucher_cat,
            email=self.customer.user.email,
            personal=True,
            )
        return voucher

    def disable_voucher(self):
        self.voucher.disable()
