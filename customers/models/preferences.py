# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from coffees.models import CoffeeType, BrewMethod, Flavor
from .customer import Customer


class Preferences(models.Model):

    GRINDED = 'GR'
    WHOLEBEANS = 'WB'
    DRIP_BAGS = 'DR'
    BOTTLED = 'BO'
    BREW_BAG = 'BB'

    PACKAGE_CHOICES = (
        (GRINDED, _('Ground (200g)')),
        (WHOLEBEANS, _('Wholebeans (200g)')),
        (DRIP_BAGS, _('Drip bags (x10)')),
        (BREW_BAG, _('Brew bags (x10)')),
        (BOTTLED, _('Bottled (x6)')),
    )

    customer = models.OneToOneField(Customer)

    coffee = models.ForeignKey(CoffeeType,
        null=True,
        blank=True,
        )

    flavor = models.ManyToManyField(Flavor,
        blank=True
        )

    brew = models.ForeignKey(BrewMethod,
        null=True,
        blank=True,
        )

    package = models.CharField(
        verbose_name=_('Packaging method'),
        max_length=16,
        choices=PACKAGE_CHOICES,
        default=WHOLEBEANS
        )

    decaf = models.BooleanField(
        verbose_name=_('Decaffeinated?'),
        default=False)

    different = models.BooleanField(
        verbose_name=_('Different?'),
        default=False)

    different_pods = models.BooleanField(
        verbose_name=_('Different Pods?'),
        default=False)

    cups = models.PositiveIntegerField(
        verbose_name=_('Cups per week'),
        default=7)

    intense = models.PositiveIntegerField(
        verbose_name=_('Intense'),
        default=5)

    interval = models.PositiveIntegerField(
        verbose_name=_('Shipping Interval'),
        default=7)

    interval_pods = models.PositiveIntegerField(
        verbose_name=_('Shipping Interval for Pods'),
        default=7)

    force_coffee = models.BooleanField(
        verbose_name=_('Force sending Bag choosen by client'),
        default=False)

    force_coffee_pods = models.BooleanField(
        verbose_name=_('Force sending Pod choosen by client'),
        default=False)

    present_next = models.BooleanField(
        verbose_name=_('Make next order free'),
        default=False)

    class Meta:
        verbose_name_plural = _('Preferences')
        default_permissions = ('add', 'change', 'export', 'delete')

    def __unicode__(self):
        return self.customer.user.get_full_name()
