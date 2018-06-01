# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from datetime import timedelta

from django_hstore import hstore

from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

from coffees.models import BrewMethod, CoffeeType

from .base_order import BaseOrder
from .preferences import Preferences


CTZ = timezone.get_current_timezone()


class Order(BaseOrder):

    FEEDBACK_CHOICES = (
        ('UP', 'Happy'),
        ('DOWN', 'Unhappy')
    )

    coffee = models.ForeignKey(CoffeeType)

    different = models.BooleanField(
        verbose_name='Different?',
        default=False)

    amount = models.DecimalField(
        verbose_name='Amount',
        max_digits=6,
        decimal_places=2,
        default=18)

    interval = models.PositiveIntegerField(
        verbose_name='Shipping Interval',
        default=14)

    recurrent = models.BooleanField(
        verbose_name='Recurrent?',
        default=False)

    # TODO: move existing feedback to review and remove it
    feedback = models.CharField(
        max_length=16,
        choices=FEEDBACK_CHOICES,
        null=True,
        blank=True)

    brew = models.ForeignKey(BrewMethod)

    package = models.CharField(
        verbose_name='Packaging method',
        max_length=16,
        choices=Preferences.PACKAGE_CHOICES,
        default=Preferences.GRINDED)

    details = hstore.DictionaryField(default={}, blank=True)
    objects = hstore.HStoreManager()

    resent = models.BooleanField(
        verbose_name='Resent Order?',
        default=False)

    custom_price = models.BooleanField(
        verbose_name='Custom Price?',
        default=False)

    def __unicode__(self):
        return '[{}] {} | {} | {} | {} | {}'.format(
            self.id,
            self.get_status_display(),
            timezone.localtime(self.date).strftime('%b, %d (%H:%M)'),
            timezone.localtime(self.shipping_date).strftime('%b, %d (%H:%M)'),
            self.customer,
            self.coffee,
        )

    def save(self, *args, **kwargs):
        if (self.coffee.is_discovery_pack and
                'discovery_coffees' not in self.details):
            self.update_discovery_coffees(commit=False)
        super(Order, self).save(*args, **kwargs)

    @property
    def is_editable(self):
        now = CTZ.normalize(timezone.now())
        is_friday = now.isoweekday() == 5
        shipping_date_is_monday = self.shipping_date.isoweekday() == 1
        next_48h = now + timedelta(hours=48)
        next_96h = now + timedelta(hours=96)
        if (self.recurrent and
            not (is_friday and shipping_date_is_monday and
                 next_96h > self.shipping_date) and
                (next_48h < self.shipping_date)):
            return True
        return False

    @property
    def is_paused(self):
        return self.status == self.PAUSED

    @property
    def is_first_order(self):
        """Check if this order is the first customer order."""
        is_first = False
        try:
            is_first = self.id == self.customer.orders.earliest('id').id
        except Order.DoesNotExist:
            pass
        return is_first

    def hours_to_change(self):
        """Return hours left to make changes to this order."""
        uneditable_at = self.shipping_date - timedelta(hours=48)
        delta = CTZ.normalize(uneditable_at) - CTZ.normalize(timezone.now())
        delta_hrs = int(delta.total_seconds() / 3600)
        return 1 if delta_hrs == 0 else delta_hrs

    def get_next_shipping_date(self, after=None):
        now = after or CTZ.normalize(timezone.now())
        possible_day = now + timedelta(days=self.interval)
        day = possible_day.isoweekday()
        today = possible_day.replace(hour=12, minute=0, second=0, microsecond=0)
        # noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
        # morning = True if now < noon else False

        # Mon, Tue, Wed, Thu, Fri
        if day in range(1, 6):
            # return today if morning else tomorrow
            return today
        # Saturday
        elif day == 6:
            return today + timedelta(days=2)
        # Sunday
        elif day == 7:
            return today + timedelta(days=1)

    def get_after_next_shipping_date(self):
        return self.get_next_shipping_date(after=self.shipping_date)

    def get_discovery_coffee_ids(self):
        return json.loads(self.details['discovery_coffees'])

    def update_discovery_coffees(self, commit=True):
        self.details['discovery_coffees'] = [
            c.id for c in (CoffeeType.objects.discovery_pack(self.customer))]
        if commit:
            self.save(update_fields=['details'])

    @cached_property
    def discovery_coffees(self):
        coffee_ids = self.get_discovery_coffee_ids()
        coffees = CoffeeType.objects.filter(id__in=coffee_ids)
        reviews = {review.coffee.id: review
                   for review in self.reviews.filter(coffee_id__in=coffee_ids)}
        for coffee in coffees:
            coffee.review = reviews.get(coffee.id, {})
        return coffees
