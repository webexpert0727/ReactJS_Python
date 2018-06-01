# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import random
import string
from datetime import datetime, timedelta

from django.db import models
from django.utils import timezone

from coffees.models import CoffeeType

from customauth.models import MyUser
from customers.models import (
    Order, Voucher, VoucherCategory,
    Preferences, EmailManagement, Referral,
    Customer,)

from get_started.models import GetStartedResponse

from giveback_project.helpers import get_estimated_date

from loyale.models import Point

logger = logging.getLogger(__name__)

LINK_PREFIX = 'https://hookcoffee.com.sg/getstarted/?email='
BREW_LINKS = {
    'French press': 'https://www.youtube.com/watch?v=lPA_teaMKaE',
    'Stove top': 'https://www.youtube.com/watch?v=TBaNhmemifc',
    'Aeropress': 'https://www.youtube.com/watch?v=tKsQ0aDlqIU',
    'Drip': 'https://www.youtube.com/watch?v=i9Nh3GUDlpo',
    'Espresso': 'https://www.youtube.com/watch?v=hqVJ3Z-TZ1c',
}
DEFAULT_YOUTUBE_PAGE = 'https://www.youtube.com/channel/UCY8KoIHOQlpwrD-F_lWO3Cg'
BREW_TYPES = {
    "Espresso": "bags",
    "Drip": "bags",
    "Aeropress": "bags",
    "French press": "bags",
    "Stove top": "bags",
    "Nespresso": "pods",
    "Cold Brew": "bags",
    "None": "drip",
}

class BaseReminder(models.Model):

    class Meta:
        abstract = True

    username = models.CharField(max_length=32)
    order = models.ForeignKey(Order, blank=True, null=True)
    email = models.EmailField()
    from_email = models.CharField(
        max_length=100,
        default='Hook Coffee <hola@hookcoffee.com.sg>')
    subject = models.CharField(max_length=100)
    template_name = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    resumed = models.DateTimeField(blank=True, null=True)
    scheduled = models.DateTimeField()
    completed = models.BooleanField(default=False)
    voucher = models.ForeignKey(Voucher, blank=True, null=True)

    def __unicode__(self):
        return '{} [{} => {}] : {}'.format(
            self.email,
            timezone.localtime(self.created).strftime('%b, %d (%H:%M)'),
            timezone.localtime(self.scheduled).strftime('%b, %d (%H:%M)'),
            self.subject,
        )


class Reminder(BaseReminder):
    recommended_coffee = models.ForeignKey(CoffeeType, blank=True, null=True)

    def is_resume_reminder(self):
        return True if self.order else False

    def get_created(self):
        return _format_date(self.created)
    get_created.short_description = 'Created'

    def get_scheduled(self):
        return _format_date(self.scheduled)
    get_scheduled.short_description = 'Scheduled'

    def get_resumed(self):
        return _format_date(self.resumed) if self.resumed else None
    get_resumed.short_description = 'Resumed'

    def get_vars(self):
        result = {}
        if self.is_resume_reminder():

            if self.order.coffee.roasted_on:
                roasted_date = datetime.strftime(
                    self.order.coffee.roasted_on, '%d/%m/%y')
            else:
                roasted_date = ''

            if self.order.coffee.is_pods:
                packaging = "Nespresso compatible pods"
            else:
                packaging = {
                    Preferences.GRINDED: "ground coffees",
                    Preferences.WHOLEBEANS: "whole beans",
                    Preferences.DRIP_BAGS: "drip coffee bags"
                }.get(self.order.package, "whole beans")

            next_scheduled_date = self.order.shipping_date + timedelta(days=self.order.interval)

            v60 = self.order.details.get('V60STARTER')

            result = {
                'USERNAME': self.order.customer.first_name,
                'RESUME_DATE': datetime.strftime(self.resumed or timezone.now(), '%d/%m/%y'),
                'COFFEE': str(self.order.coffee),
                'ROASTED_ON': roasted_date,
                'BREW': self.order.brew.name,
                'PACKAGE': packaging,
                'SHIPPING_DATE': "{} {}".format(
                    datetime.strftime(self.order.shipping_date, '%B'),
                    ordinal(self.order.shipping_date.day)
                ),
                'NEXT_SCHEDULED_DATE': "{} {}".format(
                    datetime.strftime(next_scheduled_date, '%B'),
                    ordinal(next_scheduled_date.day)
                ),
                'NEXT_SCHEDULED_WEEKDAY': datetime.strftime(next_scheduled_date, "%A"),
                'PRICE': '%s SGD' % self.order.amount,
                'DOMAIN_NAME': 'hookcoffee.com.sg',
                'ESTIMATED_DELIVERY': get_estimated_date(self.order.shipping_date),
                'V60': v60,
                'COFFEE_NAME': self.order.coffee.name,
                'BLEND': self.order.coffee.blend,
                'REGION': self.order.coffee.region,
                'COUNTRY': self.order.coffee.country.name.__str__(),
            }

        else:
            try:
                user = MyUser.objects.get_by_natural_key(self.email)
                points = Point.objects.get(user=user).points
            except (MyUser.DoesNotExist, Point.DoesNotExist):
                points = 0

            try:
                gs_response = GetStartedResponse.objects.filter(email=self.email).latest('created')
            except GetStartedResponse.DoesNotExist:
                brew_title = 'None'
                intensity = 3
            else:
                brew_title = gs_response.form_details.get('brew_title', 'None')
                intensity = gs_response.form_details.get('intensity', 3)

            result = {
                'USERNAME': self.username.title(),
                'EMAIL': self.email,
                'BREW': brew_title,
                'INTENSITY': intensity,
                'REGURL': '%s%s' % (LINK_PREFIX, self.email),
                'POINTS': points,
                'BREW_LINK': BREW_LINKS.get(brew_title, DEFAULT_YOUTUBE_PAGE),
                'BREW_TYPE': BREW_TYPES.get(brew_title, 'bags'),
                'VOUCHER': self.voucher.name if self.voucher else '',
                'RECOMMENDEDCOFFEE': self.recommended_coffee.name if self.recommended_coffee else '',
                'ADDRESS_NAME': "self.order.shipping_address['name']",
            }

        return result

    @classmethod
    def generate_voucher(self, username, email=""):
        name = "{}{}{}".format(
            username[:20].replace(" ", "").upper(),
            "".join(random.sample("QWERTYUIOPASDFGHJKLZXCVBNM", 5)),
            "$2"
            )
        voucher_cat = VoucherCategory.objects.get(name="Re-engagement")
        personal = len(email) > 0
        voucher = Voucher.objects.create(
            name=name,
            email=email,
            discount2=12,
            category=voucher_cat,
            personal=personal
            )
        return voucher

    def disable_voucher(self):
        if self.voucher:
            self.voucher.disable()


class ReminderSkipDelivery(BaseReminder):

    token = models.CharField(max_length=64, default="dummy")

    def save(self, *args, **kwargs):
        if not self.pk:
            self.token = self._create_link_skip_delivery()
        super(ReminderSkipDelivery, self).save(*args, **kwargs)

    def get_vars(self):
        next_delivery_at = datetime.strftime(self.order.get_next_shipping_date(), '%d %B %Y')

        brew = self.order.brew.name
        package = {
            Preferences.GRINDED: "Ground for {}".format(brew),
            Preferences.WHOLEBEANS: "Wholebeans",
            Preferences.DRIP_BAGS: "Drip bags",
        }.get(self.order.package, "Drip bags")

        ref_obj, _ = Referral.objects.get_or_create(
            user=self.order.customer.user,
            defaults={'code': Referral.get_random_code(customer=self.order.customer)}
        )

        result = {
            'FNAME': self.username.title(),
            'COFFEE': self.order.coffee.name,
            'PACKAGE': package,
            'PRICE': 'S$ %s' % self.order.amount,
            'ADDRESS_NAME': self.order.shipping_address['name'],
            'LINE1': self.order.shipping_address['line1'],
            'COUNTRY_POSTCODE': self.order.shipping_address['postcode'],
            'NEXT_DELIVERY': next_delivery_at,
            'LINK_TO_SKIP_DELIVERY': 'http://{}/management/{}'.format("hookcoffee.com.sg", self.token),
            'REFERRAL_CODE': ref_obj.code,
            'ESTIMATED_DELIVERY': get_estimated_date(self.order.shipping_date),
            'SHIPPING_DATE': "{} {}".format(
                datetime.strftime(self.order.shipping_date, '%B'),
                ordinal(self.order.shipping_date.day)
            ),
        }

        return result

    def __unicode__(self):
        return '<{}> | order [{}] | "{}"'.format(
            self.email,
            self.order.id,
            self.subject,
        )

    def _create_link_skip_delivery(self):
        print 'EmailManagement created in _create_link_skip_delivery()'
        logger.debug('EmailManagement created in _create_link_skip_delivery()')
        token = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(64))
        customer = self.order.customer
        action = {'skip': True}

        EmailManagement.objects.create(token=token, customer=customer, action=action, order=self.order)

        return token


class ReminderSMS(models.Model):

    FROM_NUMBER = "6596259741"
    MESSAGE = "Hey %s\n\nSam from Hook Coffee here.\nJust wanted to check in to see if you have received your first bag of coffee and all is good with it!\nAnd if there is anything you need help with, please feel free to drop us a note or call back on this number.\nWe will be more than happy to help!\n\nBest,\nSam\n\nHook Coffee"

    customer = models.ForeignKey(Customer)
    message = models.CharField(max_length=612)
    date = models.DateTimeField(auto_now_add=True)
    scheduled = models.DateTimeField()
    sent = models.BooleanField(default=False)
    error = models.CharField(max_length=256, null=True, blank=True)

    def __unicode__(self):
        return "{} - {}".format(self.customer.user.email, self.number)

    @property
    def order(self):
        return self.customer.orders.all().earliest('date')

    @property
    def number(self):
        return self.customer.phone

    def save(self, *args, **kwargs):
        if not self.pk:
            self.scheduled += timezone.timedelta(days=7)
            logger.info("Scheduled sms for number {} <{}> on {}".format(
                self.number,
                self.customer.user.email,
                self.scheduled
                )
            )
        super(ReminderSMS, self).save(*args, **kwargs)


def _format_date(date):
    return timezone.localtime(date).strftime('%b, %d (%H:%M)')

def ordinal(n):
    if 10 <= n % 100 < 20:
        return str(n) + 'th'
    else:
        return  str(n) + {1 : 'st', 2 : 'nd', 3 : 'rd'}.get(n % 10, "th")
