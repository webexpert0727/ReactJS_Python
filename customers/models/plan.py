# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

import stripe
from giveback_project.settings import base
from django_hstore import hstore


INTERVALS = (
    ('day', 'day'),
    ('week', 'week'),
    ('month', 'month'),
    ('year', 'year')
)

class Plan(models.Model):
    plan = models.CharField('Plan ID', max_length=32, unique=True)
    name = models.CharField(max_length=255, blank=True)
    currency = models.CharField(max_length=4, default='SGD', blank=True)
    amount = models.IntegerField(help_text='in cent')
    metadata = hstore.DictionaryField(default={}, blank=True)
    interval = models.CharField(max_length=16, choices=INTERVALS, default='week')
    interval_count = models.IntegerField(default=1)
    stripe_id = models.CharField("Stripe plan ID", max_length=64, blank=True,\
                                 editable=False)

    def save(self, *args, **kwargs):
        stripe.api_key = base.SECRET_KEY
        
        if not self.stripe_id:
            print '[+] Creating plan {}'.format(self.plan)

            self.stripe_id = stripe.Plan.create(
                amount=self.amount,
                interval=self.interval,
                interval_count=self.interval_count,
                name=self.name,
                currency=self.currency,
                id=self.plan,
            ).id

        else:
            print '[+] Updating plan {}'.format(self.plan)

            try:
                current_plan = stripe.Plan.retrieve(self.stripe_id)
                current_plan.name = self.name
                current_plan.metadata = self.metadata
                current_plan.save()
            except stripe.error.CardError, e:
                # Since it's a decline, stripe.error.CardError will be caught
                body = e.json_body
                err  = body['error']

                print "Status is: %s" % e.http_status
                print "Type is: %s" % err['type']
                print "Code is: %s" % err['code']
                # param is '' in this case
                print "Param is: %s" % err['param']
                print "Message is: %s" % err['message']
            except stripe.error.RateLimitError, e:
                # Too many requests made to the API too quickly
                print e
            except stripe.error.InvalidRequestError, e:
                # Invalid parameters were supplied to Stripe's API
                print e
            except stripe.error.AuthenticationError, e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                print e
            except stripe.error.APIConnectionError, e:
                # Network communication with Stripe failed
                print e
            except stripe.error.StripeError, e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                print e
            except Exception, e:
                # Something else happened, completely unrelated to Stripe
                print e

        return super(Plan, self).save(*args, **kwargs)
        

    def __unicode__(self):
        return '{} ({} {})'.format(self.plan, self.amount, 'cent')
        
