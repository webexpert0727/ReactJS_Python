# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from django_hstore import hstore, query

from coffees.models import CoffeeType, CoffeeGear, BrewMethod

from .order import Order
from .gear_order import GearOrder


class CommonReview(models.Model):
    rating = models.IntegerField(null=True, blank=True)
    comment = models.TextField(max_length=1024, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    hidden = models.BooleanField(default=False)

    class Meta:
        abstract = True


class CoffeeReview(CommonReview):
    # was OneToOneField, for discovery pack changed to ForeignKey
    order = models.ForeignKey(Order, related_name='reviews')
    # for easy/quick access from coffee model:
    coffee = models.ForeignKey(CoffeeType, related_name='reviews')
    brew = models.ForeignKey(BrewMethod, related_name='reviews', blank=True, null=True)

    class Meta:
        ordering = ['-id']
        unique_together = ('order', 'coffee')
        default_permissions = ('add', 'change', 'export', 'delete')

    def __unicode__(self):
        return '[%s] %s' % (self.coffee.name, self.rating)

    def save(self, *args, **kwargs):
        # if coffee rated on 3 or less
        # check the customer on an active orders (discovery pack)
        # and the orders have reviewed coffee if it so:
        # force change the coffee in d.pack to another one
        if self.rating <= 3:
            customer = self.order.customer
            orders = customer.orders.filter(
                coffee__discovery=True,
                status__in=[Order.ACTIVE, Order.PAUSED])
            for order in orders:
                if self.coffee.id in order.get_discovery_coffee_ids():
                    order.update_discovery_coffees()

            if self.rating == 1:
                self.hidden = True

        super(CoffeeReview, self).save(*args, **kwargs)


# class GearReview(CommonReview):
#     order = models.OneToOneField(GearOrder, related_name='review')
#     gear = models.ForeignKey(CoffeeGear, related_name='reviews')

#     class Meta:
#         ordering = ['-id']

#     def __unicode__(self):
#         return '[%s] %s' % (self.gear.name, self.rating)
