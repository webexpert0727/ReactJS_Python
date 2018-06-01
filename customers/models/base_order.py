# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.db import models
from django.forms.models import model_to_dict
from django.utils.functional import cached_property

from .address import Address
from .customer import Customer
from .voucher import Voucher


class BaseOrder(models.Model):

    ACTIVE = 'AC'
    SHIPPED = 'SH'
    PAUSED = 'PA'
    CANCELED = 'CA'
    ERROR = 'ER'
    DECLINED = 'DE'

    STATUS_CHOICES = (
        (ACTIVE, 'Active'),
        (SHIPPED, 'Shipped'),
        (PAUSED, 'Paused'),
        (CANCELED, 'Canceled'),
        (ERROR, 'Failed'),
        (DECLINED, 'Declined')
    )

    customer = models.ForeignKey(Customer, related_name='%(class)ss')
    date = models.DateTimeField('Creation Date', auto_now_add=True)
    shipping_date = models.DateTimeField('Shipping date', null=True, blank=True)
    status = models.CharField('Status', max_length=16, choices=STATUS_CHOICES, default=ACTIVE)
    voucher = models.ForeignKey(Voucher, null=True, blank=True, on_delete=models.SET_NULL)
    address = models.ForeignKey(Address, related_name='%(class)ss', null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['-shipping_date']
        default_permissions = ('add', 'change', 'export', 'delete')

    @cached_property
    def shipping_address(self):
        if self.address:
            return model_to_dict(self.address)

        primary_address = self.customer.addresses.filter(is_primary=True)

        if (primary_address.exists() and
                'force_base_address' not in self.details):
            return model_to_dict(primary_address.get())

        address = {
            'name': 'Base address',
            'recipient_name': self.customer.get_full_name(),
            'id': -1,
            # 'is_primary': True,
            'country': self.customer.country,
            'line1': self.customer.line1,
            'line2': self.customer.line2,
            'postcode': self.customer.postcode,
        }
        return address

    @cached_property
    def shipped_to(self):
        shipped_to = self.details.get('shipped_to')
        if shipped_to:
            return json.loads(shipped_to)
        addr = self.shipping_address
        addr['country'] = addr['country'].name
        return addr

    def update_shipped_to(self, address):
        addr = {
            'recipient_name': address['recipient_name'],
            'country': str(address['country'].name),
            'line1': address['line1'],
            'line2': address['line2'],
            'postcode': address['postcode'],
        }
        self.details['shipped_to'] = json.dumps(addr)
        self.save()
