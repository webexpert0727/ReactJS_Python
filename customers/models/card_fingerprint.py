# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from .customer import Customer


class CardFingerprint(models.Model):
    # why no OneToOneField? because customer can has a
    # few cards in the past in one in the present
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    fingerprint = models.CharField(_('Card fingerprint'), max_length=128)

    def __unicode__(self):
        return '[%s] %s' % (self.fingerprint, self.customer)
