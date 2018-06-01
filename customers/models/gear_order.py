# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_hstore import hstore, query

from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from datetime import datetime

from coffees.models import CoffeeGear, WorkShops

from .base_order import BaseOrder


class GearOrderQuerySet(query.HStoreQuerySet):

    def count(self):
        return reduce(
            (lambda x, y: x + y.details.get('Quantity', 1)),
            self,
            0
        )


class GearOrderManager(hstore.HStoreManager):

    def get_queryset(self):
        # for calling custom QuerySet methods from the manager
        return GearOrderQuerySet(self.model, using=self._db)

    def count(self):
        return self.get_queryset().count()


class GearOrder(BaseOrder):

    gear = models.ForeignKey(CoffeeGear)
    # TODO: rename `price` to `amount` and move to parent class
    price = models.DecimalField(max_digits=6, decimal_places=2)
    details = hstore.DictionaryField(schema=[
        {
            'name': 'Colour',
            'class': 'CharField',
            'kwargs': {
                'blank': True,
                'max_length': 30
            }
        },
        {
            'name': 'Quantity',
            'class': 'IntegerField',
            'kwargs': {
                'default': 1
            }
        },
        {
            'name': 'packaging',
            'class': 'CharField',
            'kwargs': {
                'blank': True,
                'max_length': 30
            }
        },
        {
            'name': 'brew_method',
            'class': 'CharField',
            'kwargs': {
                'blank': True,
                'max_length': 30
            }
        },
        {
            'name': 'staff_remarks',
            'verbose_name': 'Remarks for Packing team',
            'class': 'TextField',
            'kwargs': {
                'blank': True,
                'max_length': 256,
            }
        },
        {
            'name': 'gift_note',
            'verbose_name': 'Christmas gift note',
            'class': 'TextField',
            'kwargs': {
                'blank': True,
                'max_length': 600,
            }
        },
        {
            'name': 'Pre-Order',
            'class': 'BooleanField',
            'kwargs': {
                'default': False
            }
        },
        # {
        #     'name': 'shipped_to',
        #     'class': 'CharField',
        #     'kwargs': {
        #         'blank': True,
        #         'max_length': 1000
        #     }
        # },
    ])
    tracking_number = models.CharField(max_length=30, blank=True)

    objects = GearOrderManager()

    def __unicode__(self):
        return '[G{}] {} | {} | {} | {} | {}'.format(
            self.id,
            self.get_status_display(),
            timezone.localtime(self.date).strftime('%b, %d (%H:%M)'),
            timezone.localtime(self.shipping_date).strftime('%b, %d (%H:%M)'),
            self.customer,
            self.gear,
        )

    @cached_property
    def is_editable(self):
        return False


class WorkShopOrderManager(models.Manager):

    def get_queryset(self):
        # for calling custom QuerySet methods from the manager
         return super(WorkShopOrderManager, self).get_queryset()

    def count(self):
        return self.get_queryset().count()


class WorkShopOrder(BaseOrder):
    workshop = models.ForeignKey(WorkShops)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    scheduled_date = models.DateTimeField(_('WorkShop Scheduled Date'), default=datetime.now())
    count = models.IntegerField(_('Number Of People'), default=1)
    objects = WorkShopOrderManager()
