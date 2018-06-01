# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal
import json
import logging
import random
from datetime import datetime, timedelta

import string
import stripe

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from coffees.models import CoffeeType

from customers.models import (
    CoffeeReview, GearOrder, Order, Referral, Preferences, EmailManagement)
from customers.tasks import add_event, send_email_async
from giveback_project.helpers import get_estimated_date

from loyale.mixin import PointMixin
from loyale.models import OrderPoints, Point

from ..models import FYPOrderStats

from ..roadbull_api import main as book_pickup

from reminders.models import ReminderSkipDelivery


CTZ = timezone.get_current_timezone()
logger = logging.getLogger('order_processing')
stripe.api_key = settings.SECRET_KEY


class OrderProcessing(object):

    # Order id, after which all one-off coffee orders have been paid already
    # (charged at checkout). So this constant needed to avoid double charging.
    # Created for a case where processing a declined order with a smaller ID.
    # In the future, this constant will be removed.
    SPECIAL_ORDER_ID = 18052
    # TASTERS = CoffeeType.objects.tasters()
    EMAIL_SUMMARY_FROM = 'Sam from Hook Coffee <hola@hookcoffee.com.sg>'
    EMAIL_SUMMARY_FROM_FIRST_BAG = 'Kit from Hook Coffee <hola@hookcoffee.com.sg>'
    EMAIL_SUMMARY_SUBJECT = 'Your next bag of coffee has left the Roastery'
    EMAIL_SUMMARY_SUBJECT_FIRST_BAG = 'Your Coffee is on its way to you'
    EMAIL_SUMMARY_TEMPLATE_NORMAL = 'EJ3'
    EMAIL_SUMMARY_TEMPLATE_FIRST_BAG = 'EJ2'
    EMAIL_SUMMARY_TEMPLATE_LAST_BAG = 'Gift Recipient’s LAST BAG Confirmation Email'
    EMAIL_DECLINED_SUBJECT = 'Card Payment Error'
    EMAIL_DECLINED_TEMPLATE = 'Card Payment Error'
    EMAIL_REMINDING_TEMPLATE_SKIP_LINK = 'EJ3 with skip link'
    EMAIL_REMINDING_TEMPLATE_NO_SKIP_LINK = 'EJ3 without skip link'
    EMAIL_SUMMARY_CALENDARS_2017 = 'Advent Calendar dispatch email'

    def __init__(self, request, order):
        self.request = request
        self.order = order

        self.original_status = order.get_status_display()
        self.is_gear = isinstance(order, GearOrder)
        self.is_shotpods = bool(
            not self.is_gear and order.brew.name_en == 'Nespresso')
        self.is_bottled = bool(
            not self.is_gear and order.coffee.is_bottled())
        self.tracking_number = request.request_json.get('trackingNumber', '')
        self.now = CTZ.normalize(timezone.now())
        self.result = {}

        self.customer = order.customer
        # check if customer has an active subscription
        self.customer_is_subscriber = (
            self.customer.orders
            .filter(recurrent=True, status=Order.ACTIVE)
            .exists())

        # check is this order is first for current customer
        self.is_first = (
            self.customer.orders.filter(status=Order.SHIPPED).count() == 0)

        if order.shipping_date > (self.now + timedelta(days=3)):
            self.result['error'] = '''
                The order has the shipping date exceeding 3 following days.
                Probably the shipping date has been changed
                and the order must be sent later.'''
        elif order.status == Order.SHIPPED:
            self.result['error'] = 'The order is already processed!'
        elif order.status not in [Order.ACTIVE, Order.PAUSED, Order.DECLINED]:
            self.result['error'] = ('You can only process orders that '
                                    'are ACTIVE, PAUSED or DECLINED.')

        discounts = json.loads(self.customer.discounts.get('referral', ""))
        if discounts and not self.is_gear and not self.is_bottled:
            discount_created = parse_datetime(discounts[0][1])
            order_created = self.order.date
            if discount_created < order_created:
                self.order.amount *= Decimal(discounts[0][0]) / 100
                self.order.save()
                discounts.pop(0)
                self.customer.discounts['referral'] = discounts
                self.customer.save()

    @property
    def order_points(self):
        order_points = cache.get('ORDER_POINTS')
        if not order_points:
            order_points = OrderPoints.objects.values().latest('id')
            cache.set('ORDER_POINTS', order_points, 60 * 60 * 6)  # for 6 hours
        return order_points

    def add_event(self):
        """Fire Intercom event about processed order."""
        if self.is_gear:
            event_name = 'gear-order-processed'
            extra_event_data = {'gear-order': self.order.id}
            order_id = None
        else:
            event_name = 'order-processed'
            extra_event_data = {}
            order_id = self.order.id

        charge = self.result.get('charge', {})
        event_data = {
            'old_status': self.original_status,
            'new_status': self.order.get_status_display(),
            'stripe_charge': charge.get('id'),
            'error': self.result.get('error'),
        }
        event_data.update(extra_event_data)

        add_event.delay(
            customer_id=self.customer.id,
            event=event_name,
            data=event_data,
            order_id=order_id,
        )

    def get_number_of_points_for_order(self):
        """Return a number of beanie points for processed order."""
        prefix = 'sub' if self.customer_is_subscriber else 'one'
        if self.order.coffee.special:
            suffix = 'special'
        elif self.is_shotpods:
            suffix = 'pod'
        else:
            suffix = 'regular'
        return self.order_points['%s_%s' % (prefix, suffix)]

    def grant_points(self):
        """Grant beanie points for processed order."""
        points = self.get_number_of_points_for_order()
        PointMixin().grant_points(user=self.customer.user, points=points)

    def get_voucher_for_next_order(self):
        """Return a voucher for next order if it's expected."""
        current_voucher = self.order.voucher
        if (not current_voucher or
           (current_voucher and current_voucher.name not in ['THREE20', 'HOOK4'])):
            return

        if current_voucher.name == "THREE20":
            three20_voucher_used_times = (
                self.customer.orders
                .filter(voucher__name='THREE20',
                        status__in=[Order.ACTIVE, Order.SHIPPED])
                .count())
            if three20_voucher_used_times < 3:
                return self.order.voucher
        elif current_voucher.name == "HOOK4":
            hook4_voucher_used_times = (
                self.customer.orders
                .filter(voucher__name='HOOK4',
                        status__in=[Order.ACTIVE, Order.SHIPPED])
                .count())
            if hook4_voucher_used_times < 3:
                return self.order.voucher
        return

    def get_next_coffee(self):
        """Return coffee for next order.

        If the current order has a special coffee or actived 'different'
        option will be return a random coffee.
        In all other cases will be returned the same coffee.
        """
        if (self.order.coffee.is_discovery_pack or
           (not self.order.coffee.special and not self.order.different)):
            return self.order.coffee

        if self.is_shotpods:
            available_coffees = CoffeeType.objects.nespresso()
            if self.customer.has_decaf_orders is False:
                available_coffees = available_coffees.filter(decaf=False)
        elif self.is_bottled:
            available_coffees = CoffeeType.objects.bottled()
        else:
            available_coffees = CoffeeType.objects.bags()

        available_coffees = (available_coffees
                             .filter(special=False)
                             .exclude(id=self.order.coffee.id))

        didnt_like_coffee_ids = set(
            CoffeeReview.objects
            .filter(order__customer=self.customer, rating__lte=3)
            .values_list('coffee', flat=True))

        sample_coffees = (
            available_coffees.exclude(id__in=list(didnt_like_coffee_ids)))

        if sample_coffees.exists():
            return random.choice(sample_coffees)
        elif available_coffees.exists():
            return random.choice(available_coffees)
        return self.order.coffee

    def create_next_order(self):
        """Return a new order with the same options as current order.

        Only if current order is recurrent or coffee in order is a taster pack.
        Otherwise, a new(next) order will not be created.
        """
        if not self.order.recurrent:
            return

        coffee = self.get_next_coffee()
        new_order = Order(
            coffee=coffee,
            amount=coffee.amount,
            customer=self.customer,
            date=self.now,
            shipping_date=self.order.get_next_shipping_date(),
            recurrent=True,
            status=Order.ACTIVE,
            brew=self.order.brew,
            package=self.order.package,
            different=self.order.different,
            interval=self.order.interval)

        if 'force_base_address' in self.order.details:
            new_order.details['force_base_address'] = True

        voucher = self.get_voucher_for_next_order()
        if voucher:
            new_order.voucher = voucher
            new_order.amount = (new_order.amount * (100 - voucher.discount) /
                                100 - voucher.discount2)

        processed_by = self.result.get('processed_by')
        if (processed_by == 'present' or
           (processed_by == 'credits' and self.customer.amount > 0) or
           (processed_by == 'card' and self.customer.stripe_id)):
            new_order.save()
            self.new_order = new_order

            logger.debug('Process order: [%d][%s] Next order: %s' % (
                         self.order.id, processed_by, new_order))

        self.new_order = new_order

    def send_summary_email(self):
        """Send summary email.

        Send email if this is not first processed order and not resent,
        otherwise customer has already received "Welcome to hook coffee" email.
        """
        if self.order.resent:
            return

        roasted_at = link_to_skip_delivery = ''
        if self.order.coffee.roasted_on:
            roasted_at = datetime.strftime(self.order.coffee.roasted_on, '%d/%m/%y')

        now = self.now
        today = '{} {}'.format(
            ordinal(now.day),
            datetime.strftime(now, '%B %Y')
            )

        next_delivery_at = datetime.strftime(self.order.get_next_shipping_date(), '%d %B %Y')

        point_obj, _ = Point.objects.get_or_create(
            user=self.customer.user,
            defaults={'points': 0},
        )
        ref_obj, _ = Referral.objects.get_or_create(
            user=self.customer.user,
            defaults={'code': Referral.get_random_code(customer=self.customer)}
        )

        last_bag = bool(self.result.get('processed_by') == 'credits' and
                        self.customer.amount == 0)

        from_email = self.EMAIL_SUMMARY_FROM
        subject = self.EMAIL_SUMMARY_SUBJECT

        if last_bag:
            # if customer has not got credits in his account, send email
            # to inform customer that this would be his last bag of coffee
            template_name = self.EMAIL_SUMMARY_TEMPLATE_LAST_BAG
        elif self.is_first:
            template_name = self.EMAIL_SUMMARY_TEMPLATE_FIRST_BAG
            from_email = self.EMAIL_SUMMARY_FROM_FIRST_BAG
            subject = self.EMAIL_SUMMARY_SUBJECT_FIRST_BAG
        else:
            template_name = self.EMAIL_SUMMARY_TEMPLATE_NORMAL
            # create a link to skip next delivery
            # link_to_skip_delivery = self.create_link_skip_delivery()

        if self.is_shotpods:
            brew = 'Nespresso®'
            package = 'Nespresso® compatible pods'
        else:
            brew = self.order.brew.name
            package = {
                Preferences.GRINDED: "Ground for {}".format(brew),
                Preferences.WHOLEBEANS: "Wholebeans",
                Preferences.DRIP_BAGS: "Drip bags",
            }.get(self.order.package, "Drip bags")

        send_email_async.delay(
            subject=subject,
            template=template_name,
            to_email=self.customer.get_email(),
            from_email=from_email,
            merge_vars={
                'USERNAME': self.customer.first_name,
                'COFFEE': self.order.coffee.name,
                'ROASTED_ON': roasted_at,
                'BREW': brew,
                'PACKAGE': package,
                'PRICE': 'S$ %s' % self.order.amount,
                'SHIPPING_DATE': today,
                'ADDRESS_NAME': self.order.shipping_address['name'],
                'LINE1': self.order.shipping_address['line1'],
                'COUNTRY_POSTCODE': self.order.shipping_address['postcode'],
                'NEXT_DELIVERY': next_delivery_at,
                'POINTS': self.get_number_of_points_for_order(),
                'TOTAL_POINTS': point_obj.points,
                'ESTIMATED_DELIVERY': get_estimated_date(now),
                'REFERRAL_CODE': ref_obj.code,
                # 'LINK_TO_SKIP_DELIVERY': link_to_skip_delivery,
                'DOMAIN_NAME': self.request.META.get('HTTP_HOST'),
            },
        )

        if self.order.recurrent and self.order.interval >= 7:
            template_name = self.EMAIL_REMINDING_TEMPLATE_SKIP_LINK
            if ReminderSkipDelivery.objects.exists():
                if ReminderSkipDelivery.objects.latest('id').id % 2 != 0:
                    template_name = self.EMAIL_REMINDING_TEMPLATE_NO_SKIP_LINK

            ReminderSkipDelivery.objects.create(
                username=self.customer.first_name.title(),
                order=self.new_order,
                email=self.customer.get_email(),
                from_email='Hook Coffee Roastery <hola@hookcoffee.com.sg>',
                subject='Your upcoming Hook Coffee Order',
                template_name=template_name,
                created=now,
                scheduled=self.new_order.shipping_date - timedelta(days=4),
            )

    # def create_link_skip_delivery(self):
    #     token = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(64))
    #     customer = self.customer
    #     action = {'skip': True}

    #     EmailManagement.objects.create(token=token, customer=customer, action=action, order=self.new_order)

    #     return 'http://{}/management/{}'.format(self.request.META['HTTP_HOST'], token)

    def send_gear_email(self):
        """Send email for Cristmas calendars."""

        from_email = self.EMAIL_SUMMARY_FROM_FIRST_BAG
        subject = self.EMAIL_SUMMARY_SUBJECT_FIRST_BAG
        template_name = self.EMAIL_SUMMARY_CALENDARS_2017

        now = self.now
        today = '{} {}'.format(
            ordinal(now.day),
            datetime.strftime(now, '%B %Y')
            )

        send_email_async.delay(
            subject=subject,
            template=template_name,
            to_email=self.customer.get_email(),
            from_email=from_email,
            merge_vars={
                'USERNAME': self.customer.first_name,
                'COFFEE': self.order.gear.name,
                'SHIPPING_DATE': today,
                'PACKAGE': '',
                'ADDRESS_NAME': self.order.shipping_address['name'],
                'LINE1': self.order.shipping_address['line1'],
                'COUNTRY_POSTCODE': self.order.shipping_address['postcode'],
                'ESTIMATED_DELIVERY': get_estimated_date(now, 1, 1),
                'ROADBULL_TRACKING_NUMBER': "http://{server}/Order/Tracking/{tracking_number}".format(
                    server=settings.ROADBULL_SERVER, tracking_number=self.order.tracking_number),
                'DOMAIN_NAME': self.request.META.get('HTTP_HOST'),
            },
        )

    def log_error(self, error):
        logger.error(
            'Process order: [%d] Error: %r',
            self.order.id, error,
            exc_info=True,
            extra={
                'data': {
                    'order': self.order,
                    'customer': self.order.customer,
                }
            }
        )

    def process_as_present(self):
        """Process the current order as present (for free)."""
        self.order.amount = 0
        self.order.status = Order.SHIPPED
        self.order.save(update_fields=['amount', 'status'])

        preferences = self.customer.preferences
        preferences.present_next = False
        preferences.save(update_fields=['present_next'])

        self.result['processed_by'] = 'present'

    def process_by_credits(self):
        """Use part of credits.

        Customer has got enought credits to buy out the order.
        """
        self.customer.amount -= self.order.amount
        self.customer.save(update_fields=['amount'])

        self.order.amount = 0
        self.order.status = Order.SHIPPED
        self.order.save(update_fields=['amount', 'status'])

        self.result['processed_by'] = 'credits'

    def process_by_charge(self):
        """Charge the customer by using Stripe.

        Customer has not got enought credits to buy out the order.
        """
        try:
            with transaction.atomic():
                if self.customer.amount > 0:
                    self.order.amount -= self.customer.amount
                    self.order.save(update_fields=['amount'])
                    self.customer.amount = 0
                    self.customer.save(update_fields=['amount'])

                self.result['charge'] = stripe.Charge.create(
                    amount=int(round(self.order.amount * 100)),
                    currency='SGD',
                    customer=self.customer.stripe_id,
                    description=str(self.order.coffee),
                    metadata={'order_id': self.order.id},
                )
        except stripe.error.CardError as e:
            self.order.status = Order.DECLINED
            self.order.save(update_fields=['status'])
            self.result['error'] = e.json_body['error'].get('message')
            self.result['declined'] = True
            send_email_async.delay(
                subject=self.EMAIL_DECLINED_SUBJECT,
                template=self.EMAIL_DECLINED_TEMPLATE,
                to_email=self.customer.get_email(),
                merge_vars={
                    'USERNAME': self.customer.first_name,
                    'DOMAIN_NAME': self.request.META.get('HTTP_HOST'),
                }
            )
            self.log_error(e)
        except stripe.error.RateLimitError as e:
            self.result['error'] = (
                'Too many requests made to the API too quickly.')
            self.log_error(e)
        except stripe.error.InvalidRequestError as e:
            self.result['error'] = (
                "Invalid parameters were supplied to Stripe's API.")
            self.log_error(e)
        except stripe.error.AuthenticationError as e:
            self.result['error'] = "Authentication with Stripe's API failed."
            self.log_error(e)
        except stripe.error.APIConnectionError as e:
            self.result['error'] = 'Network communication with Stripe failed.'
            self.log_error(e)
        except stripe.error.StripeError as e:
            self.result['error'] = ('Display a very generic error to the user,'
                                    ' and maybe send yourself an email.')
            self.log_error(e)
        except Exception as e:
            self.order.status = Order.ERROR
            self.order.save(update_fields=['status'])
            self.result['error'] = 'Critical Stripe error: %r' % e
            self.log_error(e)
        else:
            self.order.status = Order.SHIPPED
            self.order.save(update_fields=['status'])
            self.result['processed_by'] = 'card'

    def process(self):
        """Processing Order / GearOrder."""
        if 'error' in self.result:  # an error could be added in init
            return self.result

        logger.debug('Process order: %s' % self.order)
        if self.is_gear:
            # one-off order has been paid already
            self.order.status = Order.SHIPPED
            self.order.tracking_number = self.tracking_number
            # use roadbull shipping for Christmas calendars
            if self.order.gear.name in [
                    'The Hook Coffee Advent Calendar',
                    'The Hook Coffee Advent Calendar (x2)']:
                book_response = book_pickup(self.order)
                if book_response and book_response.get('Code') == 0:
                    self.result['shipping-succeed'] = True
                    self.result['shipping-message'] = book_response.get('Message')
                    self.result['bar_code_url'] = book_response.get('bar_code_url')
                    self.result['qr_code_url'] = book_response.get('qr_code_url')
                    self.order.tracking_number = book_response.get('tracking_number')
                    logger.debug("Successfully booked roadbull for order id={}, tracking number: {}".format(
                        self.order.id, self.order.tracking_number))
                else:
                    self.result['shipping-succeed'] = False
                    self.result['shipping-message'] = book_response.get('Message')
                    logger.error("Failed to book Roadbull for order id={}: {}".format(
                        self.order.id, self.result['shipping-message']))

            self.order.save(update_fields=['status', 'tracking_number'])

        elif (not self.order.recurrent and
              self.order.id >= self.SPECIAL_ORDER_ID):
            # one-off order has been paid already
            self.order.status = Order.SHIPPED
            self.order.save(update_fields=['status'])

        elif self.customer.preferences.present_next:
            self.process_as_present()

        elif self.customer.amount >= self.order.amount:
            self.process_by_credits()

        else:
            self.process_by_charge()

        self.add_event()
        if 'error' not in self.result and not self.is_gear:
            self.create_next_order()
            self.grant_points()
            self.send_summary_email()
            FYPOrderStats.objects.create(order=self.order)  # WTF?

        if 'error' not in self.result and self.is_gear and self.order.gear.name in [
                    'The Hook Coffee Advent Calendar',
                    'The Hook Coffee Advent Calendar (x2)']:
            if self.result.get('shipping-succeed') == True:
                self.send_gear_email()
            else:
                pass
                # TODO send email confirmation (using common shipping)

        return self.result


def ordinal(n):
    if 10 <= n % 100 < 20:
        return str(n) + 'th'
    else:
        return  str(n) + {1 : 'st', 2 : 'nd', 3 : 'rd'}.get(n % 10, "th")
