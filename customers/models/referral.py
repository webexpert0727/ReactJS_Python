# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random
import string

from django.db import models
from django.core.urlresolvers import reverse

from unidecode import unidecode

from customauth.models import MyUser


class Referral(models.Model):

    GENERAL = 'GE'
    FACEBOOK = 'FB'
    AIM_CHOICES = (
        (GENERAL, 'General'),
        (FACEBOOK, 'Facebook'),
    )

    ACTIVE = 'AC'
    INACTIVE = 'NA'
    STATUS_CHOICES = (
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
    )

    user = models.ForeignKey(MyUser)
    aim = models.CharField(
        max_length=16,
        choices=AIM_CHOICES,
        default=GENERAL
    )
    code = models.CharField(max_length=64, null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=ACTIVE
    )

    class Meta:
        unique_together = ('user', 'aim')

    def __unicode__(self):
        return '{} <{}>'.format(self.aim, self.user.email)

    @classmethod
    def get_random_code(cls, customer):
        return ''.join([
            '_'.join(unidecode(customer.first_name).split()).upper(),
            str(customer.user.id),
            ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        ])

    def get_absolute_url(self):
        return '%s?ref=%s' % (reverse('get_started'), self.code)


class Reference(models.Model):
    referred = models.ForeignKey(MyUser, related_name='Referrer')
    referrer = models.ForeignKey(MyUser, related_name='Referred')

    def __unicode__(self):
        return '<{}> <-- <{}>'.format(self.referred.email, self.referrer.email)

    class Meta:
        unique_together = ('referrer', 'referred')
