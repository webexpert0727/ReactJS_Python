# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging
import os
import sys
from collections import Counter, OrderedDict
from datetime import datetime, timedelta

from dateutil.parser import parse as parse_dt

import stripe

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateformat import format as dt_format

from customauth.models import MyUser

from customers.models import Customer, Order, GearOrder
from customers.tasks import send_email_async

from loyale.models import RedemItem


CTZ = timezone.get_current_timezone()
logger = logging.getLogger('giveback_project.' + __name__)
stripe.api_key = settings.SECRET_KEY


def validate(request, method):
    if request.method is not method:
        RESULT_JSON = {}

        RESULT_JSON['status'] = 405
        RESULT_JSON['error_message'] = "Invalid Method"

        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


def serialize_order(order):
    details = {}

    if isinstance(order, Order):
        customer = order.customer
        product = order.coffee
        created_at = order.date
        details['type'] = 'COFFEE'
        details['brew_method'] = order.brew.name
        details['packaging_method'] = order.package
        order.details.pop('shipped_to', None)  # don't show
        details['remarks'] = order.details
        if order.voucher and order.voucher.name in settings.GIFT_VOUCHERS:
            details['gift'] = order.voucher.name
    elif isinstance(order, GearOrder):
        customer = order.customer
        product = order.gear
        created_at = order.date
        details['type'] = 'GEAR'
        details['brew_method'] = '-'
        details['packaging_method'] = '-'
        order.details.pop('shipped_to', None)  # don't show
        details['remarks'] = {
            k: v if v not in ('true', 'false') else v.capitalize()
            for k, v in order.details.items()
        }
        if order.voucher and order.voucher.name in settings.GIFT_VOUCHERS:
            details['gift'] = order.voucher.name
    elif isinstance(order, RedemItem):
        customer = order.user.customer
        product = order.item
        created_at = order.added
        details['type'] = 'REDEM'
        details['brew_method'] = '-'
        details['packaging_method'] = '-'
        details['remarks'] = order.points

    shipping_at = order.shipping_date

    details['id'] = order.id
    details['customer_id'] = customer.id
    details['name'] = customer.get_full_name()
    details['email'] = customer.get_email()
    details['coffee'] = product.name
    details['created_date'] = int(dt_format(created_at, 'U'))
    details['shipping_date'] = int(dt_format(shipping_at, 'U'))
    details['status'] = order.status  # order.get_status_display()
    return details


def serialize_orders(order_set, brew_method=None, order_by=None):
    orders = []
    for order in order_set:
        order_details = serialize_order(order)
        # if no filter condition specified, display all
        # or only display orders according to specified brew method(s)
        if not brew_method or order_details['brew_method'] in brew_method:
            orders.append(order_details)

    if not order_by:
        order_by = lambda o: (o['shipping_date'], o['coffee'])

    orders = sorted(orders, key=order_by, reverse=True)
    return orders


def order_count_json(start_date, end_date, order_set, brew_method_filter=None):
    dateOrderCount = {}

    while start_date <= end_date:
        dateOrderCount[str(start_date)] = 0
        start_date = start_date + timedelta(days=1)

    try:
        for order in order_set:
            brew_name = order.brew.name
            orderDate = order.shipping_date
            if not brew_method_filter or brew_name in brew_method_filter:
                for date in dateOrderCount.keys():
                    if isSameDay(datetime.strptime(date, "%Y-%m-%d").date(), orderDate):
                        dateOrderCount[date] += 1

    except Exception as e:
        sys.stderr.write(str(e))

    return OrderedDict(sorted(dateOrderCount.items()))


def customer_json(customers):
    result_json = []

    for customer in customers:
        curr_customer = {}
        curr_customer['customer_id'] = customer.id
        curr_customer['customer_name'] = customer.get_full_name()
        curr_customer['customer_email'] = customer.user.email
        result_json.append(curr_customer)

    return result_json


def isSameDay(date1, date2):
    return (date1.year == date2.year and
            date1.month == date2.month and
            date1.day == date2.day)


def get_week(date):
    """Return the full week (Sunday first) of the week containing the given date.

    'date' may be a datetime or date instance (the same type is returned).
    """
    one_day = timedelta(days=1)
    day_idx = (date.weekday() + 1) % 7  # turn sunday into 0, monday into 1, etc.
    sunday = date - timedelta(days=day_idx)
    date = sunday
    for n in xrange(7):
        yield date
        date += one_day


def getOrderIdAndHashFromFilePath(filepath):
    # filepath: <orderId>.<hashOfOrder/Address>.pdf
    return map(lambda x: str(x), os.path.splitext(filepath)[0].split('.'))


def deleteExistingOrderLabelPdf(id):
    try:
        labels_path = settings.LABELS_PATH
        files_in_dir = os.listdir(labels_path)
        for file in files_in_dir:
            order_id_hash = getOrderIdAndHashFromFilePath(file)
            if order_id_hash[0] == str(id):
                os.remove(os.path.join(labels_path, file))
    except Exception as e:
        print e


def deleteExistingOrderAddressPdf(id):
    try:
        address_path = settings.ADDRESS_PATH
        files_in_dir = os.listdir(address_path)
        for file in files_in_dir:
            order_id_hash = getOrderIdAndHashFromFilePath(file)
            if order_id_hash[0] == str(id):
                os.remove(os.path.join(address_path, file))

    except Exception as e:
        print e


def hasOwnLabel(order):
    if isinstance(order, Order) and order.coffee.hasLabel:
        return True
    return False


def send_replacement_email(request, order):
    send_email_async.delay(
        subject='Hold on tight! It is coming!',
        template='Your replacement order is on its way to you!',
        to_email=order.customer.get_email(),
        merge_vars={
            'USERNAME': order.customer.first_name,
            'DOMAIN_NAME': request.META.get('HTTP_HOST'),
        }
    )


def getNextShippingDate(original_shipping_date, interval):

    ctz = timezone.get_current_timezone()
    original_shipping_date = ctz.normalize(original_shipping_date)

    now = ctz.normalize(timezone.now())

    if interval:
        possible_day = original_shipping_date.replace(hour=12, minute=0, second=0, microsecond=0) + timedelta(interval)
    else:
        possible_day = now.replace(hour=12, minute=0, second=0, microsecond=0) + timedelta(days=1)

    tomorrow = possible_day.replace(
        hour=12, minute=0, second=0, microsecond=0) + timedelta(days=1)
    two_days_later = possible_day.replace(
        hour=12, minute=0, second=0, microsecond=0) + timedelta(days=2)
    three_days_later = possible_day.replace(
        hour=12, minute=0, second=0, microsecond=0) + timedelta(days=3)

    current_shipping_date = possible_day
    day = possible_day.isoweekday()

    if day == 5:
        # Friday
        current_shipping_date = three_days_later

    elif day == 6:
        # Saturday
        current_shipping_date = two_days_later

    elif day == 7:
        current_shipping_date = tomorrow

    return current_shipping_date


def customerEmailToCustomerDict(customer_email):
    return {
        'customer_email': customer_email
    }


def diff_month(d1, d2):
    return (d1.year - d2.year)*12 + d1.month - d2.month


def generate_month_year_tuples(numtuples):
    curr_month = datetime.now().month
    curr_year = datetime.now().year

    month_years = []

    while curr_year > 0 and numtuples > len(month_years):
        while curr_month > 0 and numtuples > len(month_years):
            month_years.append((curr_month, curr_year))
            curr_month = curr_month - 1
        curr_year = curr_year - 1
        curr_month = 12

    return month_years


def month_in(year, months, field='shipping_date'):
    q = Q(**{field + '__year': year})
    for m in months:
        q |= Q(**{field + '__month': m})
    return q


def countOrdersByDate(start_date, end_date):
    query_end_date = end_date + timedelta(days=1)

    orders = Order.objects.filter(shipping_date__gte=start_date,
                                  shipping_date__lt=query_end_date,
                                  status__in=['AC', 'SH', 'PA'])

    return len(orders)


def getNumberOfNewSignupsByDate(start_date, end_date):

    query_end_date = end_date + timedelta(days=1)

    # retrieve all users that created accounts within specified date range
    users = MyUser.objects.filter(created_at__gte=start_date,
                                  created_at__lt=query_end_date)

    return len(users)


def getNumberOfActiveCustomersByDate(start_date, end_date):

    # retrieve distinct customers that made at least 1 order within the specified date range
    return Customer.objects.filter(
        orders__shipping_date__gte=start_date,
        orders__shipping_date__lt=end_date + timedelta(days=1),
        orders__status__in=['AC', 'SH', 'PA']).distinct().count()


def getNumberOfChurnCustomersByDate(start_date, end_date):

    # retrieve distinct customers that made at least 1 order within the specified date range
    query_end_date = end_date + timedelta(days=1)
    customers = Customer.objects.filter(
        orders__shipping_date__gte=start_date,
        orders__shipping_date__lt=query_end_date,
        orders__status__in=['AC', 'SH', 'PA']).distinct()

    num_churn = 0

    for customer in customers:

        # get latest order within specified date range
        latest_order = Order.objects.filter(shipping_date__gte=start_date,
                                            shipping_date__lt=query_end_date,
                                            ).latest('shipping_date')

        shipping_date_latest_order = latest_order.shipping_date

        four_weeks_later = shipping_date_latest_order + timedelta(weeks=4)

        # check whether customer has active, shipped or paused order within the next 4 weeks
        # if customer does not have, customer is considered churn
        order = Order.objects.filter(shipping_date__gte=shipping_date_latest_order,
                                     shipping_date__lt=four_weeks_later + timedelta(days=1),
                                     customer=customer,
                                     status__in=['AC', 'SH', 'PA'])
        if len(order) == 0:
            num_churn += 1

    return num_churn


def parse_datetime(timestr):
    return CTZ.localize(parse_dt(timestr, dayfirst=True))


def customers_with_multiple_orders(date, show_backlog):
    date_lt = date + timedelta(days=2)
    valid_statuses = [Order.ACTIVE, Order.PAUSED, Order.SHIPPED]
    if show_backlog:
        date_gte = datetime(2015, 1, 1, tzinfo=CTZ)
        valid_statuses.pop(-1)
    else:
        date_gte = date + timedelta(days=1)
    coffees = (Order.objects
               .filter(status__in=valid_statuses,
                       shipping_date__range=(date_gte, date_lt))
               .values_list('customer_id', flat=True))
    gears = (GearOrder.objects
             .filter(status=Order.ACTIVE,
                     shipping_date__range=(date_gte, date_lt))
             .exclude(gear__special='christmas')
             .values_list('customer_id', flat=True))
    redems = (RedemItem.objects
              .filter(status='pending')
              .values_list('user__customer__id', flat=True))
    customer_ids = [cid for ids in [coffees, gears, redems] for cid in ids]
    return [cid for cid, count in Counter(customer_ids).items() if count > 1]
