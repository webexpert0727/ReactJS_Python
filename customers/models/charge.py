# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django_hstore import hstore
from django.utils import timezone

from . import Customer
from coffees.models import CoffeeType

STATUS=(
    ('new', 'new'),
    ('done', 'done'),
    )

class Charge(models.Model):
    customer = models.ForeignKey(Customer)
    product = models.ForeignKey(CoffeeType)
    amount = models.CharField(max_length=32, blank=True)
    description = models.CharField(max_length=255, blank=True)
    metadata = hstore.DictionaryField('Metadata', default={}, blank=True)
    date = models.DateTimeField(default=timezone.now, blank=True)
    # status = models.CharField(max_length=32, choices=STATUS)
    stripe_id = models.CharField("Stripe charge ID", max_length=255, blank=True)
    

    def __unicode__(self):
        return "{}, {}, {}".format(self.customer, self.product, self.amount)

    # def save(self, *args, **kwargs):
    #     if not self.id:
    #         self.created = timezone.now()
    #     return super(Charge, self).save(*args, **kwargs)
