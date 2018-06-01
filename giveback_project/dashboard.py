# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import random
from datetime import datetime, timedelta
from math import ceil

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from coffees.models import BrewMethod, CoffeeSticker, CoffeeType
from customers.models import Customer, GearOrder, Order, Preferences, Voucher
from customers.tasks import add_event
from giveback_project.helpers import geo_check
from loyale.mixin import PointMixin
from loyale.models import OrderPoints, RedemItem
from reminders.models import Reminder

from .labels import (generate_address_label, generate_all_address_labels,
                     generate_all_product_labels,
                     generate_common_product_label, generate_product_label,
                     generate_qr_all_coffees)

logger = logging.getLogger(__name__)
point_mixin = PointMixin()
stripe.api_key = settings.SECRET_KEY

ctz = timezone.get_current_timezone()

MAX_LABELS_IN_FILE = settings.MAX_LABELS_IN_FILE


@staff_member_required
def dashboard(request):
    """
    Administration dashboard.

    Here we process the orders, take money from clients, create subsequent orders if needed.
    If a coffee is running out here we switch users to another coffee type.
    """

    ctz = timezone.get_current_timezone()
    now = ctz.normalize(timezone.now())
    day = now.isoweekday()

    # today = now.replace(
    #     hour=12, minute=0, second=0, microsecond=0)
    tomorrow = now.replace(
        hour=12, minute=0, second=0, microsecond=0) + timedelta(days=1)
    two_days_later = now.replace(
        hour=12, minute=0, second=0, microsecond=0) + timedelta(days=2)
    three_days_later = now.replace(
        hour=12, minute=0, second=0, microsecond=0) + timedelta(days=3)

    current_shipping_date = tomorrow
    if day == 5:
        # Friday
        current_shipping_date = three_days_later

    elif day == 6:
        # Saturday
        current_shipping_date = two_days_later

    coffees_all = CoffeeType.objects.all()
    coffees_active = CoffeeType.objects.filter(special=False).filter(mode=True)

    # Get non Nespresso orders
    orders = Order.objects.filter(
        customer__country='SG',
        shipping_date__lte=current_shipping_date,
        brew__in=BrewMethod.objects.exclude(name_en='Nespresso'),
        status__in=[Order.ACTIVE, Order.PAUSED, Order.ERROR, Order.DECLINED])\
        .order_by('status', 'coffee', 'brew', 'package')

    orders_with_labels = Order.objects.filter(
        shipping_date__lte=current_shipping_date,
        status__in=[Order.ACTIVE, Order.PAUSED, Order.ERROR])\
        .order_by('coffee', 'brew', 'package')\
        .exclude(coffee__label__exact='', coffee__label_drip__exact='')\
        .count()
    labels_by_parts = range(1, int(ceil(orders_with_labels / float(MAX_LABELS_IN_FILE))) + 1)

    # Get Nespresso Pods orders
    orders_pods = Order.objects.filter(
        customer__country='SG',
        shipping_date__lte=current_shipping_date,
        brew=BrewMethod.objects.get(name_en='Nespresso'),
        status__in=[Order.ACTIVE, Order.PAUSED, Order.ERROR, Order.DECLINED])\
        .order_by('status', 'coffee', 'brew', 'package')

    # Gear orders
    orders_gear = GearOrder.objects.filter(
        customer__country='SG',
        shipping_date__lte=current_shipping_date,
        status__in=[Order.ACTIVE, Order.PAUSED, Order.ERROR, Order.DECLINED])\
        .order_by('status')

    redemption_items = RedemItem.objects.filter(
        shipping_date__lte=current_shipping_date,
        status='pending')\
        .exclude(item__name='Free bag of coffee')

    worldwide_orders = Order.objects.filter(
        shipping_date__lte=current_shipping_date,
        # brew__in=BrewMethod.objects.exclude(name='Nespresso'),
        status__in=[Order.ACTIVE, Order.PAUSED, Order.ERROR, Order.DECLINED])\
        .exclude(customer__country='SG')\
        .order_by('status', 'coffee', 'brew', 'package')

    worldwide_orders_gear = GearOrder.objects.filter(
        shipping_date__lte=current_shipping_date,
        status__in=[Order.ACTIVE, Order.PAUSED, Order.ERROR, Order.DECLINED])\
        .exclude(customer__country='SG')\
        .order_by('status')

    worldwide_bags_customers = {}
    for order in worldwide_orders:
        if order.customer in worldwide_bags_customers.keys():
            worldwide_bags_customers[order.customer].append(order)
        else:
            worldwide_bags_customers[order.customer] = [order]

    context = {
        'orders': orders,
        'worldwide_orders': worldwide_orders,
        'labels_by_parts': labels_by_parts,
        'orders_pods': orders_pods,
        'redemptions': redemption_items,
        'coffees_all': coffees_all,
        'coffees_active': coffees_active,
        'gift_vouchers': settings.GIFT_VOUCHERS,
        'worldwide_bags_customers': worldwide_bags_customers,
        'orders_gear': orders_gear,
        'worldwide_orders_gear': worldwide_orders_gear,
        'current_domain': Site.objects.get_current().domain,
        'pagename' : 'old dashboard'
        }

    if request.method == 'POST':
        if 'do-switch-coffee' in request.POST:
            switch_coffee(request)
        elif 'order-id' in request.POST:
            process_order(request, context)
        elif 'redemption-id' in request.POST:
            redemption_id = request.POST['redemption-id']
            redemption = RedemItem.objects.get(id=redemption_id)
            redemption.status = 'done'
            redemption.save()
        else:
            context['error'] = 'No order found with given id'

    return render(request, 'dashboard.html', context)


def switch_coffee(request):
    """ Switch users to another coffee """

    coffee_from = request.POST.get('coffee-from')
    coffee_to = request.POST.get('coffee-to')
    if coffee_from and coffee_to:
        old_coffee = CoffeeType.objects.get(id=coffee_from)
        goal_coffee = CoffeeType.objects.get(id=coffee_to)
        if goal_coffee:

            # Change coffee in upcoming orders
            orders_to_change = Order.objects.filter(coffee=coffee_from)\
                .filter(status__in=['AC', 'PA', 'ER', 'DE'])
            for o in orders_to_change:
                o.coffee = goal_coffee
                o.save()

            # Change coffee in user Preferences
            preferences_to_change = Preferences.objects.filter(coffee=coffee_from)
            for p in preferences_to_change:
                p.coffee = goal_coffee
                p.save()

            # Send emails to notify user theis coffee has been changed
            for o in orders_to_change:
                goal_email = o.customer.user.email

                msg = EmailMessage(
                    subject="We hope you don't mind, we'll be sending you something different!",
                    to=[goal_email],
                    from_email='Hook Coffee <hola@hookcoffee.com.sg>')
                msg.template_name = 'Running out of Coffee'
                msg.merge_vars = {
                    goal_email: {
                        'USERNAME': o.customer.first_name,
                        'OLD_COFFEE': '%s' % old_coffee,
                        'NEW_COFFEE': '%s' % goal_coffee,
                        'DOMAIN_NAME': request.META['HTTP_HOST']},
                }
                msg.send()

                logger.debug('SWITCH COFFEE: Mailchimp template: {}, email_to: {}'.format(msg.template_name, goal_email))


def process_order(request, context={}):
    if context.get('is_gear'):
        order_id = None
        gear_order_id = context.get('order-id')
        order = GearOrder.objects.get(id=int(gear_order_id))
    else:
        order_id = context.get('order-id') or request.POST.get('order-id')
        gear_order_id = None
        order = Order.objects.get(id=int(order_id))

    # check is this order is first for current customer
    is_first = Order.objects.filter(customer=order.customer, status='SH').count() == 0 or False
    is_second = Order.objects.filter(customer=order.customer, status='SH').count() == 1 or False
    # is_third = Order.objects.filter(customer=order.customer, status='SH').count() == 2 or False
    customer = order.customer

    logger.debug('PROCESS LOCAL ORDER: order id: {}, customer: {}, country: {}'.format(order.id, customer, customer.country))

    charge = {}
    order_orig_status = order.get_status_display()
    coffee_sample = request.POST.get('coffee-sample-id')
    if coffee_sample:
        coffee_sample = CoffeeType.objects.get(id=coffee_sample)

    now = ctz.normalize(timezone.now())
    three_days_later = now.replace(
        hour=12, minute=0, second=0, microsecond=0) + timedelta(days=3)

    if order and order.status == Order.SHIPPED:
        context['error'] = 'The order is already processed!'
    elif order and (order.shipping_date > three_days_later):
        context['error'] = '''The order has the shipping date exceeding 3 following days.
                              Probably the shipping date has been changed
                              and the order must be sent later.'''
    elif (gear_order_id and order and order.status in [GearOrder.ACTIVE, GearOrder.PAUSED, GearOrder.DECLINED]):

        # one-off order has been paid already
        order.status = GearOrder.SHIPPED
        order.tracking_number = request.POST.get('tracking-number', '')
        order.save()

    elif order and order.status in [Order.ACTIVE, Order.PAUSED, Order.DECLINED]:

        # Check if customer has active subscription
        is_subscriber = Order.objects.filter(
            customer=customer,
            recurrent=True,
            status=Order.ACTIVE).exists()

        preferences = customer.preferences
        next_order = None
        next_order_voucher = None
        if is_subscriber:
            try:
                three20_voucher = Voucher.objects.get(name='THREE20')
            except Voucher.DoesNotExist:
                three20_voucher = None
            # subsequent voucher
            if order.voucher == three20_voucher:
                # count used THREE20 vouchers
                count = Order.objects.filter(customer=customer, voucher=three20_voucher, status__in=[Order.ACTIVE, Order.SHIPPED]).count()
                if count < 3:
                    next_order_voucher = three20_voucher

        # order is a coffee bag, not nespresso pods
        if order.brew.name_en != 'Nespresso':
            # need for creating next order
            if order.recurrent or (order.coffee.name == 'Taster pack' and preferences.force_coffee):
                # FIXME: .force_coffee deprecated, keeped only for old orders based on prefs.
                next_order = Order(
                    customer=customer,
                    date=datetime.now(),
                    shipping_date=order.get_next_shipping_date(),
                    recurrent=True,
                    status=Order.ACTIVE,
                    brew=order.brew,
                    package=order.package,
                    different=order.different,
                    interval=order.interval)
                # point_mixin.coffee_points(user, order.coffee)

                if (order.coffee.special or order.different):
                    another_coffee = random.choice(
                        CoffeeType.objects
                        .bags()
                        .filter(special=False)
                        .exclude(id=order.coffee.id))
                    next_order.coffee = another_coffee
                    next_order.amount = another_coffee.amount
                else:
                    next_order.coffee = order.coffee
                    next_order.amount = order.coffee.amount

                if 'force_base_address' in order.details:
                    next_order.details['force_base_address'] = True

                if next_order_voucher:
                    next_order.voucher = next_order_voucher
                    next_order.amount = next_order.amount * (100 - next_order.voucher.discount) / 100 - next_order.voucher.discount2

            # FIXME: CHANGE ORDER ID on actual when the new UI will be deployed
            if not order.recurrent and order.id >= 18052:
                # one-off order has been paid already
                order.status = Order.SHIPPED
                order.save()

                # grant some points for processed order
                if order.coffee.special:
                    points = OrderPoints.objects.latest('id').one_special
                else:
                    points = OrderPoints.objects.latest('id').one_regular
                point_mixin.grant_points(user=customer.user, points=points)

            # (1) should present current order for free
            elif preferences.present_next:
                order.amount = 0
                order.status = Order.SHIPPED
                order.save()

                preferences.present_next = False
                preferences.save()

                # save subscriptional order if exists
                if next_order:
                    next_order.save()
                    logger.debug('order_id={} [present_next] Next order saved: next_id={}, {}'.format(order.id, next_order.id, next_order))

                # send email in 5 days if this is the first processed order for current customer
                if is_first:
                    Reminder.objects.create(
                        username=customer.first_name.upper(),
                        email=customer.user.email,
                        from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                        subject='Welcome to Hook Rewards',
                        template_name='O3 - Welcome to Hook Rewards (done)',
                        scheduled=now + timedelta(days=5))
                else:
                    # send email if this is not first processed order
                    # otherwise user has already received "Welcome to hook coffee" email
                    roasted_date = ''
                    if order.coffee.roasted_on:
                        roasted_date = datetime.strftime(order.coffee.roasted_on, '%d/%m/%y')

                # sent automatically 3 days after customer get their second bag sent out
                if is_second:
                    Reminder.objects.create(
                        username=customer.first_name.upper(),
                        email=customer.user.email,
                        from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                        subject='Let us create a better experience for you',
                        template_name='O4 - survey on subscription (done)',
                        scheduled=now + timedelta(days=3))

                # sent automatically 2 working days after customer third order is processed
                # if is_third:
                #     Reminder.objects.create(
                #         username=customer.first_name.upper(),
                #         email=customer.user.email,
                #         from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                #         subject='Welcome to Hook Rewards',
                #         template_name='04 - 2 days after third order sent (done)',
                #         scheduled=now + timedelta(days=2))

            # (2) customer has got enought credits to buy out the order
            elif customer.amount >= order.amount:
                customer.amount -= order.amount
                customer.save()

                order.amount = 0
                order.status = Order.SHIPPED
                order.save()

                # grant some points for processed order
                if order.coffee.special:
                    if is_subscriber:
                        points = OrderPoints.objects.latest('id').sub_special
                    else:
                        points = OrderPoints.objects.latest('id').one_special
                else:
                    if is_subscriber:
                        points = OrderPoints.objects.latest('id').sub_regular
                    else:
                        points = OrderPoints.objects.latest('id').one_regular

                point_mixin.grant_points(user=customer.user, points=points)

                if customer.amount > 0 and next_order:
                    next_order.save()
                    logger.debug('order_id={} [customer.amount >= order.amount] Next order saved: next_id={}, {}'.format(order.id, next_order.id, next_order))

                roasted_date = ''
                if order.coffee.roasted_on:
                    roasted_date = datetime.strftime(order.coffee.roasted_on, '%d/%m/%y')

                if order.customer.amount > 0 and not is_first:
                    template_name = 'O2 - subsequent order on subscription (done)'
                    subject = 'Your next bag of coffee has left the Roastery'
                else:
                    template_name = 'Gift Recipient’s LAST BAG Confirmation Email'
                    subject = 'Your next bag of coffee is leaving the Roastery!'

                # send another email in 5 days if this is the first processed order for current customer
                # sent automatically 5 working days after customer gets their first order
                if is_first:
                    Reminder.objects.create(
                        username=customer.first_name.upper(),
                        email=customer.user.email,
                        from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                        subject='Welcome to Hook Rewards',
                        template_name='O3 - Welcome to Hook Rewards (done)',
                        scheduled=now + timedelta(days=5))

                # sent automatically 3 days after customer get their second bag sent out
                if is_second:
                    Reminder.objects.create(
                        username=customer.first_name.upper(),
                        email=customer.user.email,
                        from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                        subject='Let us create a better experience for you',
                        template_name='O4 - survey on subscription (done)',
                        scheduled=now + timedelta(days=3))

                # sent automatically 2 working days after customer third order is processed
                # if is_third:
                #     Reminder.objects.create(
                #         username=customer.first_name.upper(),
                #         email=customer.user.email,
                #         from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                #         subject='Welcome to Hook Rewards',
                #         template_name='04 - 2 days after third order sent (done)',
                #         scheduled=now + timedelta(days=2))

            # (3) customer has not got enought credits to buy out the order
            else:
                order.amount -= customer.amount
                order.save()
                customer.amount = 0
                customer.save()

                price = int(round(order.amount * 100))

                # process order in stripe
                try:
                    charge = stripe.Charge.create(
                        amount=price,
                        currency='SGD',
                        customer=customer.stripe_id,
                        description='%s' % order.coffee,
                        metadata={}
                    )

                    order.status = Order.SHIPPED
                    order.save()

                    # grant some points for processed order
                    if order.coffee.special:
                        if is_subscriber:
                            points = OrderPoints.objects.latest('id').sub_special
                        else:
                            points = OrderPoints.objects.latest('id').one_special
                    else:
                        if is_subscriber:
                            points = OrderPoints.objects.latest('id').sub_regular
                        else:
                            points = OrderPoints.objects.latest('id').one_regular

                    point_mixin.grant_points(user=customer.user, points=points)

                    # create next subscriptional order
                    if next_order:
                        if customer.stripe_id:
                            next_order.save()
                            logger.debug('order_id={} [(3) else] Next order created: next_id={}, {}'.format(
                                order.id, next_order.id, next_order))

                    # send email in 5 days if this is the first processed order for current customer
                    if is_first:
                        Reminder.objects.create(
                            username=customer.first_name.upper(),
                            email=customer.user.email,
                            from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                            subject='Welcome to Hook Rewards',
                            template_name='O3 - Welcome to Hook Rewards (done)',
                            scheduled=now + timedelta(days=5))
                    elif order.recurrent:
                        roasted_date = ''
                        if order.coffee.roasted_on:
                            roasted_date = datetime.strftime(order.coffee.roasted_on, '%d/%m/%y')

                    # sent automatically 3 days after customer get their second bag sent out
                    if is_second:
                        Reminder.objects.create(
                            username=customer.first_name.upper(),
                            email=customer.user.email,
                            from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                            subject='Let us create a better experience for you',
                            template_name='O4 - survey on subscription (done)',
                            scheduled=now + timedelta(days=3))

                    # sent automatically 2 working days after customer third order is processed
                    # if is_third:
                    #     Reminder.objects.create(
                    #         username=customer.first_name.upper(),
                    #         email=customer.user.email,
                    #         from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                    #         subject='Welcome to Hook Rewards',
                    #         template_name='04 - 2 days after third order sent (done)',
                    #         scheduled=now + timedelta(days=2))

                except stripe.error.CardError, e:
                    # since it's a decline, stripe.error.CardError will be caught
                    order.status = Order.DECLINED
                    order.save()

                    logger.error('order_id={} Stripe Card error: {}, order: {}'.format(order.id, e, order))

                    body = e.json_body
                    err = body['error']
                    context['error'] = err['message']

                except stripe.error.RateLimitError, e:
                    context['error'] = 'Too many requests made to the API too quickly.'
                except stripe.error.InvalidRequestError, e:
                    context['error'] = "Invalid parameters were supplied to Stripe's API."
                except stripe.error.AuthenticationError, e:
                    context['error'] = "Authentication with Stripe's API failed."
                except stripe.error.APIConnectionError, e:
                    context['error'] = "Network communication with Stripe failed."
                except stripe.error.StripeError, e:
                    context['error'] = "Display a very generic error to the user,\
                        and maybe send yourself an email."
                except Exception as e:
                    context['error'] = 'Critical Stripe error.', e
                    order.status = Order.ERROR
                    order.save()

        # order is nespresso pods
        else:
            if order.recurrent:
                next_order = Order(
                    customer=customer,
                    date=datetime.now(),
                    shipping_date=order.get_next_shipping_date(),
                    recurrent=True,
                    status=Order.ACTIVE,
                    brew=BrewMethod.objects.get(name_en='Nespresso'),
                    package=order.package,
                    different=order.different,
                    interval=order.interval)

                if (order.coffee.special or order.different):
                    available_coffees = (
                        CoffeeType.objects
                        .nespresso()
                        .filter(special=False)
                        .exclude(id=order.coffee.id))

                    if customer.has_decaf_orders is False:
                        available_coffees = available_coffees.filter(decaf=False)

                    another_coffee = random.choice(available_coffees)
                    next_order.coffee = another_coffee
                    next_order.amount = another_coffee.amount
                else:
                    next_order.coffee = order.coffee
                    next_order.amount = order.coffee.amount

                if 'force_base_address' in order.details:
                    next_order.details['force_base_address'] = True

                if next_order_voucher:
                    next_order.voucher = next_order_voucher
                    next_order.amount = next_order.amount * (100 - next_order.voucher.discount) / 100 - next_order.voucher.discount2

            # FIXME: CHANGE ORDER ID on actual when the new UI will be deployed
            if not order.recurrent and order.id >= 18052:
                # one-off order has been paid already
                order.status = Order.SHIPPED
                order.save()

                # grant some points for processed order
                if order.coffee.special:
                    points = OrderPoints.objects.latest('id').sub_pod
                else:
                    points = OrderPoints.objects.latest('id').one_pod
                point_mixin.grant_points(user=customer.user, points=points)

            # (1) present current order
            elif preferences.present_next:
                order.amount = 0
                order.status = Order.SHIPPED
                order.save()
                preferences.present_next = False
                preferences.save()

                # Create next subscription order
                if next_order:
                    next_order.save()
                    logger.debug('order_id={} [present_next] Next order saved: next_id={}, {}'.format(order.id, next_order.id, next_order))

                # send email in 5 days if this is the first processed order for current customer
                if is_first:
                    Reminder.objects.create(
                        username=customer.first_name.upper(),
                        email=customer.user.email,
                        from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                        subject='Welcome to Hook Rewards',
                        template_name='O3 - Welcome to Hook Rewards (done)',
                        scheduled=now + timedelta(days=5))
                else:
                    # send email if this is not first processed order
                    # otherwise user has already received "Welcome to hook coffee" email
                    roasted_date = ''
                    if order.coffee.roasted_on:
                        roasted_date = datetime.strftime(order.coffee.roasted_on, '%d/%m/%y')

                # sent automatically 3 days after customer get their second bag sent out
                if is_second:
                    Reminder.objects.create(
                        username=customer.first_name.upper(),
                        email=customer.user.email,
                        from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                        subject='Let us create a better experience for you',
                        template_name='O4 - survey on subscription (done)',
                        scheduled=now + timedelta(days=3))

                # sent automatically 2 working days after customer third order is processed
                # if is_third:
                #     Reminder.objects.create(
                #         username=customer.first_name.upper(),
                #         email=customer.user.email,
                #         from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                #         subject='Welcome to Hook Rewards',
                #         template_name='04 - 2 days after third order sent (done)',
                #         scheduled=now + timedelta(days=2))

            # (2) Use part of credits
            elif customer.amount >= order.amount:
                print 'Use part of credits'
                customer.amount -= order.amount
                customer.save()

                order.amount = 0
                order.status = Order.SHIPPED
                order.save()

                # Grant beanie points for processed order
                if is_subscriber:
                    points = OrderPoints.objects.latest('id').sub_pod
                else:
                    points = OrderPoints.objects.latest('id').one_pod

                point_mixin.grant_points(user=customer.user, points=points)
                print 'Granted on checkout (nespresso)', points, 'to', customer.user

                if customer.amount > 0 and next_order:
                    next_order.save()
                    logger.debug('order_id={} [customer.amount >= order.amount] Next order saved: next_id={}, {}'.format(order.id, next_order.id, next_order))

                roasted_date = ''
                if order.coffee.roasted_on:
                    roasted_date = datetime.strftime(order.coffee.roasted_on, '%d/%m/%y')

                if order.customer.amount > 0 and not is_first:
                    template_name = 'O2 - subsequent order on subscription (done)'
                    subject='Your next bag of coffee has left the Roastery'
                else:
                    template_name = 'Gift Recipient’s LAST BAG Confirmation Email'
                    subject='Your next bag of coffee is leaving the Roastery!'

                # send another email in 5 days if this is the first processed order for current customer
                if is_first:
                    Reminder.objects.create(
                        username=customer.first_name.upper(),
                        email=customer.user.email,
                        from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                        subject='Welcome to Hook Rewards',
                        template_name='O3 - Welcome to Hook Rewards (done)',
                        scheduled=now + timedelta(days=5))

                # sent automatically 3 days after customer get their second bag sent out
                if is_second:
                    Reminder.objects.create(
                        username=customer.first_name.upper(),
                        email=customer.user.email,
                        from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                        subject='Let us create a better experience for you',
                        template_name='O4 - survey on subscription (done)',
                        scheduled=now + timedelta(days=3))

                # sent automatically 2 working days after customer third order is processed
                # if is_third:
                #     Reminder.objects.create(
                #         username=customer.first_name.upper(),
                #         email=customer.user.email,
                #         from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                #         subject='Welcome to Hook Rewards',
                #         template_name='04 - 2 days after third order sent (done)',
                #         scheduled=now + timedelta(days=2))

            # (3) Use all credits
            else:
                print 'Use all credits'
                order.amount -= customer.amount
                order.save()
                customer.amount = 0
                customer.save()

                price = int(round(order.amount * 100))
                try:
                    charge = stripe.Charge.create(
                        amount=price,
                        currency='SGD',
                        customer=customer.stripe_id,
                        description='%s' % order.coffee,
                        metadata={}
                    )

                    order.status = Order.SHIPPED
                    order.save()

                    # Grant beanie points for processed order
                    if is_subscriber:
                        points = OrderPoints.objects.latest('id').sub_pod
                    else:
                        points = OrderPoints.objects.latest('id').one_pod

                    point_mixin.grant_points(user=customer.user, points=points)

                    if next_order:
                        # Create next subscription order
                        if customer.stripe_id:
                            # Check if user has entered his credit card details
                            next_order.save()
                            logger.debug('order_id={} [(3) else] Next order created: next_id={}, {}'.format(
                                order.id, next_order.id, next_order))

                    # send email in 5 days if this is the first processed order for current customer
                    if is_first:
                        Reminder.objects.create(
                            username=customer.first_name.upper(),
                            email=customer.user.email,
                            from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                            subject='Welcome to Hook Rewards',
                            template_name='O3 - Welcome to Hook Rewards (done)',
                            scheduled=now + timedelta(days=5))
                    elif order.recurrent:
                        roasted_date = ''
                        if order.coffee.roasted_on:
                            roasted_date = datetime.strftime(order.coffee.roasted_on, '%d/%m/%y')

                    # sent automatically 3 days after customer get their second bag sent out
                    if is_second:
                        Reminder.objects.create(
                            username=customer.first_name.upper(),
                            email=customer.user.email,
                            from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                            subject='Let us create a better experience for you',
                            template_name='O4 - survey on subscription (done)',
                            scheduled=now + timedelta(days=3))

                    # sent automatically 2 working days after customer third order is processed
                    # if is_third:
                    #     Reminder.objects.create(
                    #         username=customer.first_name.upper(),
                    #         email=customer.user.email,
                    #         from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                    #         subject='Welcome to Hook Rewards',
                    #         template_name='04 - 2 days after third order sent (done)',
                    #         scheduled=now + timedelta(days=2))

                except stripe.error.CardError, e:
                    # Since it's a decline, stripe.error.CardError will be caught
                    order.status = Order.DECLINED
                    order.save()

                    body = e.json_body
                    err = body['error']
                    context['error'] = err['message']

                except stripe.error.RateLimitError, e:
                    context['error'] = 'Too many requests made to the API too quickly.'
                except stripe.error.InvalidRequestError, e:
                    context['error'] = "Invalid parameters were supplied to Stripe's API."
                except stripe.error.AuthenticationError, e:
                    context['error'] = "Authentication with Stripe's API failed."
                except stripe.error.APIConnectionError, e:
                    context['error'] = 'Network communication with Stripe failed.'
                except stripe.error.StripeError, e:
                    context['error'] = 'Display a very generic error to the user,\
                        and maybe send yourself an email.'
                except Exception as e:
                    context['error'] = 'Critical Stripe error.', e
                    order.status = Order.ERROR
                    order.save()

    if not context.get('error') and coffee_sample:
        customer.received_coffee_samples.add(coffee_sample)

    if gear_order_id:
        event_name = 'gear-order-processed'
        extra_event_data = {
            'gear-order': order.id,
        }
        order_id = None
    else:
        event_name = 'order-processed'
        extra_event_data = {}
        order_id = order.id

    event_data = {
        'old_status': order_orig_status,
        'new_status': order.get_status_display(),
        'stripe_charge': charge.get('id'),
        'error': context.get('error'),
    }
    event_data.update(extra_event_data)

    add_event.delay(
        customer_id=customer.id,
        event=event_name,
        data=event_data,
        order_id=order_id,
    )

    return order


def process_global_orders(request):
    ctz = timezone.get_current_timezone()
    now = ctz.normalize(timezone.now())
    day = now.isoweekday()

    # today = now.replace(
    #     hour=12, minute=0, second=0, microsecond=0)
    tomorrow = now.replace(
        hour=12, minute=0, second=0, microsecond=0) + timedelta(days=1)
    two_days_later = now.replace(
        hour=12, minute=0, second=0, microsecond=0) + timedelta(days=2)
    three_days_later = now.replace(
        hour=12, minute=0, second=0, microsecond=0) + timedelta(days=3)

    my_shipping_date = tomorrow
    if day == 5:
        my_shipping_date = three_days_later
    elif day == 6:
        my_shipping_date = two_days_later

    customer = Customer.objects.select_related('user').get(id=int(request.POST.get('customer')))

    orders = Order.objects.filter(
        customer=customer,
        shipping_date__lte=my_shipping_date,
        status__in=[Order.ACTIVE, Order.PAUSED, Order.ERROR])

    event_name = 'global-order-processed'

    for order in orders:
        order_orig_status = order.get_status_display()

        order.status = Order.SHIPPED
        order.save()
        logger.debug('PROCESS GLOBAL ORDER: order id: {}, customer: {}, country: {}'.format(order.id, order.customer, order.customer.country))

        if order.coffee.brew_method.name == 'Nespresso':
            points = OrderPoints.objects.latest('id').one_pod
        elif order.coffee.special:
            points = OrderPoints.objects.latest('id').one_special
        else:
            points = OrderPoints.objects.latest('id').one_regular

        point_mixin.grant_points(user=order.customer.user, points=points)
        logger.debug('GRANT BEANIE POINTS: order id: {}, customer: {}, points: {}'.format(order.id, order.customer, points))

        event_data = {
            'old_status': order_orig_status,
            'new_status': order.get_status_display(),
        }

        add_event.delay(
            customer_id=customer.id,
            event=event_name,
            data=event_data,
            order_id=order.id,
        )

    messages.add_message(request, messages.INFO, "activate worldwide tab")

    return redirect('dashboard')


@staff_member_required
@require_POST
@csrf_exempt
@geo_check
def update_order_status(request, is_worldwide):
    """Get the order id when scanning barcode.

    Updates the order status and returns address label."""
    order_id = request.POST.get('order-id')
    # if not order_id.startswith('@'):  # Leading symbol in QR code
    #     return HttpResponse('Use @, Luck!', status=400)
    # order_id = order_id.lstrip('@')
    if '@' not in order_id:
        return HttpResponse('Use @, Luck!', status=400)
    # Coffee: @600 OR https://hookcoffee.com.sg/qr-social/@600/  => 600
    # Gear: @G600 OR https://hookcoffee.com.sg/qr-social/@G600/  => G600
    order_id = order_id.rstrip('/').split('@')[-1]

    is_gear = False
    if order_id.startswith('G'):  # is GearOrder
        order_id = order_id.lstrip('G')
        is_gear = True

    context = {
        'order-id': order_id,
        'is_gear': is_gear,
        'is_worldwide': is_worldwide,
    }
    order = process_order(request, context)
    err = context.get('error')
    if err:  # FIXME: go to messages
        errmsg = (
            'An error occurred while processing the order!\n\n'
            'Order ID: {pk}\nUsername/Email: {name}\nAccount number: {acc}\n'
            'Error: {err}').format(pk=order.pk, name=order.customer,
                                   acc=order.customer.stripe_id, err=err)
        return HttpResponse(errmsg, status=406, content_type='text/plain')
    return print_address(request, order_id=order_id, is_gear=is_gear)


def print_address(request, order_id=None, is_gear=None):
    if is_gear:  # is GearOrder
        gear_order_id = order_id
        order_id = redemption_id = None
    else:
        order_id = order_id or request.POST.get('order')
        gear_order_id = request.POST.get('gear-order-id')
        redemption_id = request.POST.get('redemption')

    if order_id:
        order = Order.objects.get(id=order_id)
    elif redemption_id:
        order = RedemItem.objects.get(id=redemption_id)
    elif gear_order_id:
        order = GearOrder.objects.get(id=gear_order_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = \
        'attachment; filename=address_%d.pdf' % order.id

    label_buffer = generate_address_label(order)
    response.write(label_buffer.getvalue())

    return response


def print_all_addresses(request):
    ctz = timezone.get_current_timezone()
    now = ctz.normalize(timezone.now())
    today = now.replace(hour=12, minute=0, second=0, microsecond=0)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = \
        'attachment; filename=addresses_%s.pdf' % today.strftime('%Y-%m-%d')

    labels_buffer = generate_all_address_labels()
    response.write(labels_buffer.getvalue())

    return response


def qr_social(request, order_id=None):
    context = {'sticker': {
        'name': CoffeeSticker._meta.get_field('name').get_default(),
        'description': CoffeeSticker._meta.get_field('description').get_default(),
        'caption': CoffeeSticker._meta.get_field('caption').get_default(),
        'hashtag': CoffeeSticker._meta.get_field('hashtag').get_default(),
        'sticker': {
            'url': settings.MEDIA_URL + CoffeeSticker._meta.get_field('sticker').get_default()}}}
    try:
        if order_id:
            if order_id.startswith('0'):
                # if order_id have prefix '0' - is a coffee type ID in the DB
                coffee_id = order_id.lstrip('0')
            elif order_id.startswith('G'):  # Gear order
                raise ObjectDoesNotExist()
            elif order_id.startswith('R'):  # Redem order
                raise ObjectDoesNotExist()
            else:
                context['order'] = order_id
                order = Order.objects.get(id=order_id)
                coffee_id = order.coffee.id
            sticker = CoffeeSticker.objects.get(coffee_id=coffee_id)
            if sticker:
                context['sticker'] = sticker
    except ObjectDoesNotExist:
        pass

    return render(request, 'giveback_project/qr_social.html', context)


def qr_social_coffees(requests):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=qr_codes.pdf'

    pages_buffer = generate_qr_all_coffees()
    response.write(pages_buffer.getvalue())

    return response


def print_label(request):
    order_id = request.POST.get('order')
    gear_order_id = request.POST.get('gear-order-id')

    if order_id:
        order = Order.objects.get(id=order_id)
    elif gear_order_id:
        order = GearOrder.objects.get(id=gear_order_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = \
        'attachment; filename=order_%d.pdf' % order.id

    if gear_order_id or (not (order.coffee.label or order.coffee.label_drip)):
        label_buffer = generate_common_product_label(order)
    else:
        label_buffer = generate_product_label(order)

    response.write(label_buffer.getvalue())

    return response


def print_all_labels(request):
    ctz = timezone.get_current_timezone()
    now = ctz.normalize(timezone.now())
    today = now.replace(hour=12, minute=0, second=0, microsecond=0)

    special = bool(request.POST.get('special'))
    part_labels = int(request.POST.get('part'))

    filename = 'orders_{spec}{dt}{part}.pdf'.format(
        spec='special_' if special else '',
        dt=today.strftime('%Y-%m-%d'),
        part='_%d' % part_labels if part_labels else '')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename

    # provide customer for worldwide orders
    # print all labels for each customer in one go
    customer = None
    if request.POST.get('customer'):
        cid = request.POST.get('customer')
        customer = Customer.objects.get(id=cid)

    labels_buffer = generate_all_product_labels(
        special, part_labels, per_file=MAX_LABELS_IN_FILE, customer=customer)
    response.write(labels_buffer.getvalue())

    return response
