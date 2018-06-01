# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django_hstore import hstore

from giveback_project.settings import base
from .customer import Customer
from .plan import Plan

import stripe

STATUS = (
    ('active', 'active'),
    ('paused', 'paused'),
    )

class Subscription(models.Model):
    customer = models.ForeignKey(Customer)
    plan = models.ForeignKey(Plan)
    metadata = hstore.DictionaryField(default={}, blank=True)
    stripe_id = models.CharField("Stripe subscription ID", max_length=255,\
                                 blank=True, editable=False)
    status = models.CharField(max_length=32, choices=STATUS, default='active')

    def __unicode__(self):
        return '{}, {}'.format(self.customer, self.plan)

    def save(self, *args, **kwargs):
        stripe.api_key = base.SECRET_KEY

        try:
            customer = stripe.Customer.retrieve(self.customer.stripe_id)
            self.stripe_id = customer.subscriptions.create(
                                                           plan=self.plan,
                                                           metadata=self.metadata)\
                .id
        except Exception as e:
            print '[!] Create subscription failed', e
            self.stripe_id = None

        if self.stripe_id:
            return super(Subscription, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        stripe.api_key = base.SECRET_KEY
        print 'Deleting...'
        print self.stripe_id
        print self.customer.stripe_id

        try:
            customer = stripe.Customer.retrieve(self.customer.stripe_id)
            subscription = customer.subscriptions.retrieve(self.stripe_id)
            result = subscription.delete()
            print 'result: ', result
        except Exception as e:
            print e
            result = None

        # if result:
        print 'Deleting from DB'
        return super(Subscription, self).delete(*args, **kwargs)

