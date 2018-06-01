# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals

from datetime import datetime
from decimal import Decimal

from dateutil import rrule
from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.utils.dateformat import format as dt_format

from customers.models import Customer, Order


CTZ = timezone.get_current_timezone()


def to_unix_timestamp_ms(date):
        """Convert datetime to unix timestamp in microseconds.

        Alternative:
            - date.strftime('%Y-%m-%dT%H:%M:%S%fZ')
        """
        date_utc = date.replace(tzinfo=timezone.utc)
        return int(dt_format(date_utc, 'Uu'))


def get_first_dates_of_months(from_date=None, to_date=None):
    if from_date is None:
        first_order_date = Order.objects.earliest('id').date.date()
        from_date = datetime(
            first_order_date.year, first_order_date.month, 1, tzinfo=CTZ)
    if to_date is None:
        to_date = datetime.now(tz=CTZ)
    return list(rrule.rrule(freq=rrule.MONTHLY, dtstart=from_date, until=to_date))


def get_customers_signed_up_in_month(date):
    return Customer.objects.filter(
        user__created_at__range=(date, date + relativedelta(months=+1)))


def cohort_analysis(func):
    points = []
    date_by_months = get_first_dates_of_months()
    date_by_months = date_by_months[:-1]  # except the current month
    for i, date in enumerate(date_by_months):
        customers = get_customers_signed_up_in_month(date)
        signed_up_cohort = date.strftime('%Y.%m')
        # cohort_year, cohort_month = signed_up_cohort.split('.')
        for _date in date_by_months[i:]:
            time = to_unix_timestamp_ms(_date)
            value = func(_date, relativedelta(months=+1), customers, signed_up=date)
            points.append({
                'measurement': func.__name__,
                'tags': {},
                'time': time,
                'fields': {
                    signed_up_cohort: round(value, 2)
                }
            })
    return points


def app_data(func, measurement):
    points = []
    result = func()
    for point in result:
        date = to_unix_timestamp_ms(point['date'])
        values = point['values']
        tags = point.get('tags', {})
        for key, val in values.items():
            if isinstance(val, datetime):
                values[key] = to_unix_timestamp_ms(val)
            elif isinstance(val, Decimal):
                values[key] = round(val, 2)
            elif key == 'details':
                values.pop(key)
        points.append({
            'measurement': measurement,
            'tags': tags,
            'time': date,
            'fields': values,
        })
    return points
