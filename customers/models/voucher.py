# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models


class VoucherCategory(models.Model):
    name = models.CharField(max_length=50)
    desc = models.TextField(
        verbose_name="Description",
        help_text="(optional)",
        default="",
        blank=True)

    class Meta:
        verbose_name_plural = 'Voucher categories'

    def __unicode__(self):
        return self.name


class Voucher(models.Model):
    name = models.CharField(max_length=32, default='TRYUS50')
    mode = models.BooleanField('Enabled', default=True)
    discount = models.IntegerField(verbose_name='Discount (%)', help_text='percents', default=0)
    discount2 = models.IntegerField(verbose_name='Discount ($)', help_text='dollars', default=0)
    count = models.PositiveSmallIntegerField('Times used', default=0)
    category = models.ForeignKey(VoucherCategory)
    personal = models.BooleanField(default=False)
    email = models.CharField(max_length=64, null=True, blank=True, default="")

    def __unicode__(self):
        return '{} ({})'.format(self.name, self.count)

    def increment(self):
        self.count += 1
        self.save()

    def disable(self):
        self.mode = False
        self.save()
