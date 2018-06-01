# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from customauth.models import MyUser


POINT_STATUS = (
                ('add', 'Add'),
                ('minus', 'Minus')
            )


ITEM_STATUS = (
                ('pending', 'Pending'),
                ('done', 'Done')
            )

SUBSCRIBER_STATUS = (
                ('subscribe', 'Subscribe'),
                ('none', 'Not subscribe')
            )


class SetPoint(models.Model):
    status = models.CharField(max_length=32, choices=SUBSCRIBER_STATUS)
    points = models.IntegerField(null=False, blank=False, default=0)

    class Meta:
        unique_together = ('status', 'points')


class CoffeeTypePoints(models.Model):
    status = models.CharField(max_length=32, choices=SUBSCRIBER_STATUS, blank=True, null=True)
    coffee_type = models.ForeignKey('coffees.CoffeeType')
    points = models.IntegerField(null=False, blank=False)


class Point(models.Model):
    user = models.ForeignKey(MyUser)
    points = models.IntegerField(null=False, blank=False)
    added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User's points"
        verbose_name_plural = "User's points"

    def __unicode__(self):
        return '{} = {} points'.format(self.user.email, self.points)


class Item(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    description = models.CharField(max_length=200, blank=True, null=True)
    points = models.IntegerField(default=0)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    img = models.ImageField(blank=True)
    in_stock = models.BooleanField('In Stock', default=True)

    class Meta:
        verbose_name = "Redemption items"
        verbose_name_plural = "Redemption items"

    def __unicode__(self):
        return '{} ({})'.format(self.name, self.points)


class RedemItem(models.Model):
    user = models.ForeignKey(MyUser, related_name='redems')
    status = models.CharField(max_length=32, choices=ITEM_STATUS, default='pending')
    item = models.ForeignKey(Item)
    points = models.IntegerField(default=0)
    shipping_date = models.DateTimeField(
        verbose_name='Shipping date',
        null=True,
        blank=True)
    added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Orders"
        verbose_name_plural = "Orders"
        ordering = ['-shipping_date']


class RedemPointLog(models.Model):
    user = models.ForeignKey(MyUser)
    points = models.IntegerField(null=False, blank=False)
    added = models.DateTimeField(auto_now_add=True)
    item = models.ForeignKey(Item)


class GrantPointLog(models.Model):
    user = models.ForeignKey(MyUser)
    points = models.IntegerField(null=False, blank=False)
    added = models.DateTimeField(auto_now_add=True)


class OrderPoints(models.Model):
    sub_regular = models.IntegerField(
        verbose_name='Subsequent usual coffee',
        help_text='Regular coffee subscription',
        null=False,
        blank=False,
        default=200)

    sub_special = models.IntegerField(
        verbose_name='Subsequent premium coffee',
        help_text='Special coffee subscription',
        null=False,
        blank=False,
        default=300)

    sub_pod = models.IntegerField(
        verbose_name='Subsequent shotpod',
        help_text='Nespresso subscription',
        null=False,
        blank=False,
        default=200)

    one_regular = models.IntegerField(
        verbose_name='One-off usual coffee',
        help_text='Regular coffee alacarte',
        null=False,
        blank=False,
        default=50)

    one_special = models.IntegerField(
        verbose_name='One-off premium coffee',
        help_text='Special coffee alacarte',
        null=False,
        blank=False,
        default=75)

    one_pod = models.IntegerField(
        verbose_name='One-off shotpod',
        help_text='Nespresso alacarte',
        null=False,
        blank=False,
        default=50)

    credits = models.IntegerField(
        verbose_name='Gift credits',
        help_text='Benies amount for every gifted dollar',
        null=False,
        blank=False,
        default=1)

    class Meta:
        verbose_name = "Settings"
        verbose_name_plural = "Settings"


class Helper(models.Model):
    # Were emails sent on Thursday or not
    emails_rewards_sent = models.BooleanField('Were sent?', default=False)
    emails_rewards_sent_count = models.IntegerField('Emails sent last time', default=0)

    def __unicode__(self):
        return 'Sent {} emails'.format(self.emails_rewards_sent_count)\
            if self.emails_rewards_sent else 'Not sent yet'
