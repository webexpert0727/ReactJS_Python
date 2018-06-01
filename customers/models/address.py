# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_countries.fields import CountryField

from django.db import models
from django.utils.translation import ugettext_lazy as _


class Address(models.Model):
    """Customer's addresses.

    TODO: Temporarily only additional addresses.
          In the future this model should storing all customers' addresses.
    """

    customer = models.ForeignKey(
        'Customer', related_name='addresses', related_query_name="address")
    name = models.CharField(_('Address name'), max_length=255)
    recipient_name = models.CharField(_('Full name of recipient'), max_length=255)
    country = CountryField()
    line1 = models.CharField(_('First line of address'), max_length=255)
    line2 = models.CharField(
        _('Second line of address'), max_length=255, blank=True)
    postcode = models.CharField(_('Postal code'), max_length=13)
    is_primary = models.BooleanField(_('Primary address'), default=False)
    is_gift = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    def __unicode__(self):
        return '[%s] %s %s %s' % (self.name, self.line1, self.line2, self.postcode)

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.country = self.customer.country
        super(Address, self).save(*args, **kwargs)

    def get_address(self):
        return '%s %s' % (self.line1, self.line2)
    get_address.short_description = 'Address'
