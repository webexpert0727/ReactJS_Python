# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from itertools import chain
import logging
from datetime import datetime

from django_countries.fields import CountryField

from django_hstore import hstore

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.dateformat import format as dt_format
from django.utils.translation import ugettext_lazy as _

from coffees.models import CoffeeType

from customauth.models import MyUser

from .referral import Reference
from .voucher import Voucher


logger = logging.getLogger('giveback_project.' + __name__)


class CustomerManager(models.Manager):
    def active(self, *args, **kwargs):
        """Return the customers that have at least one active coffee order."""
        return self.filter(orders__status='AC', *args, **kwargs).distinct('id')

    def inactive(self, from_date=None):
        """Return inactive customers.

        Customers that have a shipped/paused order within the date specified
        to now but haven't an active orders currently.
        """
        qs = (self.filter(orders__status__in=['PA', 'SH'])
                  .exclude(orders__status='AC')
                  .distinct('id'))
        if from_date:
            qs = qs.filter(orders__shipping_date__gte=from_date)
        return qs


class Customer(models.Model):
    user = models.OneToOneField(MyUser)
    first_name = models.CharField(_('First name'), max_length=255)
    last_name = models.CharField(_('Last name'), max_length=255)
    country = CountryField()
    line1 = models.CharField(_('First line of address'), max_length=255)
    line2 = models.CharField(_('Second line of address'), max_length=255, blank=True)
    postcode = models.CharField(_('Postal code'), max_length=13)
    phone = models.CharField(_('Phone'), max_length=10, blank=True,help_text="(65xxxxxxxx)")
    amount = models.IntegerField(_('Credits'), help_text='SGD', default=0)
    stripe_id = models.CharField(_('Stripe customer ID'), max_length=255, blank=True)
    vouchers = models.ManyToManyField(Voucher, blank=True)
    card_details = models.CharField(max_length=10, default='0000000000', null=True, blank=True)
    received_coffee_samples = models.ManyToManyField(
        CoffeeType,
        blank=True,
        related_name='+')
    extra = hstore.DictionaryField(default={}, schema=[
        {
            'name': 'answered_exp_survey',
            'class': 'BooleanField',
            'kwargs': {
                'default': False
            }
        },
    ])
    objects = CustomerManager()
    discounts = hstore.DictionaryField(default={'referral': []})

    class Meta:
        default_permissions = ('add', 'change', 'export', 'delete')

    def __unicode__(self):
        return '[%s] %s %s <%s>' % (
            self.country, self.first_name, self.last_name, self.user.email)

    def get_full_name(self):
        return '%s %s' % (self.first_name, self.last_name)
    get_full_name.short_description = 'Customer'

    def get_email(self):
        return self.user.email
    get_email.short_description = 'Email'

    def get_lower_email(self):
        return self.user.email.lower()

    def get_full_address(self):
        return '%s %s' % (self.line1, self.line2)
    get_full_address.short_description = 'Address'

    def get_all_vouchers(self):
        return ' | '.join([str(v) for v in self.vouchers.all()])
    get_all_vouchers.short_description = 'Vouchers'

    def get_all_voucher_names(self):
        return ','.join([v.name for v in self.vouchers.all()])

    def get_count_orders(self):
        return self.orders.filter(status='SH').count()
    get_count_orders.short_description = 'Orders'

    def get_vouchers_name(self):
        vouchers = []
        for voucher in self.vouchers.all():
            vouchers.append(voucher.name)
        return vouchers

    def get_signed_up(self):
        return int(dt_format(self.user.created_at, 'U'))

    def get_last_login(self):
        return int(dt_format(self.user.last_login, 'U')) if self.user.last_login else None

    def get_last_order_date(self):
        try:
            last_order_date = self.orders.latest('date').date
        except ObjectDoesNotExist:
            last_order_date = None
        return int(dt_format(last_order_date, 'U')) if last_order_date else None

    def get_last_order_status(self):
        try:
            last_order_status = self.orders.latest('date').status
        except ObjectDoesNotExist:
            last_order_status = None
        return last_order_status

    def subscription_is_paused(self):
        try:
            paused = self.orders.filter(recurrent=True).latest('date').status == 'PA'
        except ObjectDoesNotExist:
            paused = False
        return paused

    def subscription_is_canceled(self):
        try:
            canceled = self.orders.filter(recurrent=True).latest('date').status == 'CA'
        except ObjectDoesNotExist:
            canceled = False
        return canceled

    def has_active_order(self):
        return self.orders.filter(status='AC').exists()

    def has_paused_order(self):
        return self.orders.filter(status='PA').exists()

    def has_shipped_order(self):
        return self.orders.filter(status='SH').exists()

    def get_total_spend(self):
        amount = self.orders.filter(status='SH').aggregate(models.Sum('amount'))
        amount = amount['amount__sum'] or 0.0
        return round(amount, 2)

    def get_tags(self):
        tags = []
        if self.user.facebookcustomer_set.exists():
            tags.append('Facebook')
        return tags

    def get_facebook_id(self):
        try:
            fb_id = self.user.facebookcustomer_set.get().facebook_id
        except ObjectDoesNotExist:
            fb_id = None
        return fb_id

    @property
    def has_decaf_orders(self):
        return self.orders.filter(
            status='SH', coffee__decaf=True).exists()

    @property
    def has_shotpods_orders(self):
        return (self.orders.filter(status__in=('SH', 'AC'),
                                   coffee__brew_method__name_en='Nespresso')
                           .distinct('coffee')
                           .exists())

    def get_tried_coffee_ids(self):
        return (
            self.orders.filter(status__in=('SH', 'AC'))
                       .distinct('coffee')
                       .order_by('coffee_id')  # or reset the default ordering
                       .values_list('coffee_id', flat=True))

    def get_coffees_hasnt_tried(self):
        not_tried_coffees = (
            CoffeeType.objects.non_tasters().exclude(id__in=self.get_tried_coffee_ids()))

        if self.has_shotpods_orders:
            # coffees only for nespresso
            not_tried_coffees = not_tried_coffees.filter(
                brew_method__name_en='Nespresso')
        else:
            # coffees for other brew methods
            not_tried_coffees = not_tried_coffees.exclude(
                brew_method__name_en='Nespresso')
        return list(not_tried_coffees)

    def get_invite_points_earned(self):
        """
        Return the number of beanie points earned for inviting friends.

        * Only from 11 December, when referral feature was updated and we start
        giving beanie points for invites.
        """
        from loyale.mixin import POINTS_FOR_INVITED_FRIEND

        friends_invited = self.get_friends_invited(
            from_date=datetime(2016, 12, 11, tzinfo=timezone.utc))
        return friends_invited * POINTS_FOR_INVITED_FRIEND

    def get_friends_invited(self, from_date=None):
        query = self.referralvoucher_set.distinct('recipient_email').all()
        if from_date:
            query = query.filter(date__gte=from_date)
        return query.count()

    def get_friends_joined(self):
        return self.user.Referrer.all().count()

    def get_credits_earned(self):
        # $5 for every friend who join
        return self.get_friends_joined() * 5

    @property
    def is_invited(self):
        has_referrence_as_invited = self.user.Referred.all().exists()
        if not has_referrence_as_invited:
            # temporary crutches to be sure that event whitout
            # a referral referrence this customer wasn't invited:
            # by checking his first order.
            try:
                referred_by = (
                    self.orders.earliest('id').details.get('referred_by'))
                if referred_by:
                    has_referrence_as_invited = True
            except ObjectDoesNotExist:
                has_referrence_as_invited = False
        return has_referrence_as_invited

    def get_preferred_brew_method(self):
        try:
            brew = self.orders.select_related('brew').latest('date').brew.name_en
        except ObjectDoesNotExist:
            try:
                brew = self.preferences.brew.name_en
            except:
                brew = 'None'
        return brew

    def get_last_cardfingerprint(self):
        try:
            fingerprint = self.cardfingerprint_set.latest('id').fingerprint
        except ObjectDoesNotExist:
            fingerprint = None
        return fingerprint

    def get_events(self):
        return self.intercomlocal_set.all()

    def _choose_coffee_for_cancellations(self, coffee_id, coffee_name_1, coffee_name_2):
        try:
            coffee_choice_1 = CoffeeType.objects.get(name=coffee_name_1)
        except CoffeeType.DoesNotExist:
            logger.error("Coffee %s couldn't be found", coffee_name_1, exc_info=True)
        else:
            if not coffee_choice_1.id in chain(self.get_tried_coffee_ids(), [coffee_id]):
                return coffee_choice_1
            else:
                try:
                    coffee_choice_2 = CoffeeType.objects.get(name=coffee_name_2)
                except CoffeeType.DoesNotExist:
                    logger.error("Coffee %s couldn't be found", coffee_name_2, exc_info=True)
                else:
                    return coffee_choice_2
        logger.error("Couldn't choose coffee from %s, %s",
                     coffee_name_1, coffee_name_2, extra={'stack': True})
        return

    def get_recommended_coffee_for_cancellations(self, order, reason):
        """Get a coffee for those who cancel subscription.

        Returns a coffee based on cancellation reason and previously tried coffees
        """
        current_order_coffee_id = order.coffee.id
        if reason == "light":
            if order.coffee.is_pods:
                return self._choose_coffee_for_cancellations(current_order_coffee_id,
                    "The Godfather ShotPods", "Hands off my Nuts! Shotpods")
            else:
                return self._choose_coffee_for_cancellations(current_order_coffee_id,
                    "Shake Your Bun Bun!", "Give me S'mores")
        elif reason == "dark":
            if order.coffee.is_pods:
                return self._choose_coffee_for_cancellations(current_order_coffee_id,
                    "Sweet Bundchen Shotpods", "Bird of Paradise Shotpods")
            else:
                return self._choose_coffee_for_cancellations(current_order_coffee_id,
                    "Guji Liya", "Eternally Grapefruit")
        elif reason == "sour":
            if order.coffee.is_pods:
                return self._choose_coffee_for_cancellations(current_order_coffee_id,
                    "The Godfather ShotPods", "Hands off my Nuts! Shotpods")
            else:
                return self._choose_coffee_for_cancellations(current_order_coffee_id,
                    "Shake Your Bun Bun!", "Give me S'mores")

        logger.error("Couldn't get recommended coffee for reason %s, %s",
                     reason, order, extra={'stack': True})
        return

    def has_bought_christmas_gift(self):
        return True if self.gearorders.filter(gear__name__startswith="The Hook Coffee Advent Calendar") else False
