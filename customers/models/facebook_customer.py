# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from giveback_project.settings.base import AUTH_USER_MODEL


class FacebookCustomer(models.Model):

    facebook_id = models.CharField(_('Facebook ID'),
                                   max_length=255)

    first_name = models.CharField(_('First name'),
                                  max_length=255)

    last_name = models.CharField(_('Last name'),
                                 max_length=255)

    email = models.EmailField(
        verbose_name=_('Email address'),
        max_length=255,
        unique=True,
    )

    gender = models.CharField(_('Gender'),
                              max_length = 255)

    customer = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        null = True,
        blank = True
    )

    def __unicode__(self):
        return '{} {} <{}>'.format(self.first_name, self.last_name, self.email, self.customer)
