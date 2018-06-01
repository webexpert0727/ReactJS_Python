# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random
import string

from django.db import models

from django_hstore import hstore

from coffees.models import CoffeeType

from customers.models import Customer


class GetStartedResponse(models.Model):
    name = models.CharField("Username", max_length=32)
    email = models.EmailField("Email address")
    form_details = hstore.DictionaryField(default={})
    ct = models.ForeignKey(CoffeeType, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    sent_emails = models.TextField(max_length=192, default="[]", blank=True, null=True)

    class Meta:
        default_permissions = ('add', 'change', 'export', 'delete')

    def __unicode__(self):
        return '{} <{}>'.format(self.name, self.email)


class GiftVoucher(models.Model):
    sender_email = models.CharField(max_length=64)
    sender_fname = models.CharField(max_length=64)
    sender_lname = models.CharField(max_length=64)
    used = models.BooleanField(default=False)
    recipient = models.CharField(max_length=64)
    amount = models.IntegerField("Credits", help_text='SGD', default=18)
    code = models.CharField(max_length=32)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '${} {}'.format(self.amount, self.recipient)


class PodsEarlyBird(models.Model):
    email = models.CharField(max_length=64)
    date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.email


class ReferralVoucher(models.Model):
    sender = models.ForeignKey(Customer)
    used = models.BooleanField(default=False)
    recipient_email = models.CharField(max_length=64)
    discount_percent = models.IntegerField(verbose_name='Discount (%)', help_text='percents', default=0)
    discount_sgd = models.IntegerField(verbose_name='Discount ($)', help_text='dollars', default=0)
    code = models.CharField(max_length=32)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_permissions = ('add', 'change', 'export', 'delete')

    def __unicode__(self):
        return '{} {}'.format(self.sender, self.recipient_email)

    @classmethod
    def get_random_code(cls, size):
        return ''.join(
            random.choice(string.ascii_uppercase + string.digits)
            for _ in range(size)
        )
