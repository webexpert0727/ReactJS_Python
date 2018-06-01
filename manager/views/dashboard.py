# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from datetime import datetime

from dateutil import rrule
from dateutil.relativedelta import relativedelta

from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateformat import format as dt_format
from django.views.decorators.http import require_GET

from customers.models import Customer, Order

from .base import BaseApiView
from ..authentication import adminOnly
from ..google_analytics import get_report_users, initialize_analyticsreporting
from ..services.dashboard import (
    getChurnRate, getLifeTimeValue, getNumberOfNewSignups,
    processActiveCustomerBreakdown, processCoffeePerformance,
    processGetRevenue, processPercentageCustomersByAge,
    processVoucherPerformance)


CTZ = timezone.get_current_timezone()


@require_GET
def coffeePerformance(request):
    RESULT_JSON = {}
    errors = []

    start_date_str = request.GET['start_date']
    end_date_str = request.GET['end_date']

    try:
        coffee_performance = processCoffeePerformance(start_date_str, end_date_str)

        RESULT_JSON['status'] = 200
        RESULT_JSON['coffee_performance'] = coffee_performance

    except Exception as e:
        errors.append(str(e))
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = errors

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


@require_GET
def voucherPerformance(request):
    RESULT_JSON = {}
    errors = []

    start_date_str = request.GET['start_date']
    end_date_str = request.GET['end_date']

    try:
        voucher_performance = processVoucherPerformance(start_date_str, end_date_str)

        RESULT_JSON['status'] = 200
        RESULT_JSON['voucher_performance'] = voucher_performance

    except Exception as e:
        errors.append(str(e))
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = errors

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


@require_GET
def percentageCustomersByAge(request):
    RESULT_JSON = {}
    errors = []

    try:
        customer_percentage_by_age = processPercentageCustomersByAge()

        RESULT_JSON['status'] = 200
        RESULT_JSON['customer_percentage_by_age'] = customer_percentage_by_age

    except Exception as e:
        errors.append(str(e))
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = errors

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


@require_GET
def usersFromGA(request):
    RESULT_JSON = {}
    errors = []

    start_date = request.GET['start_date']
    end_date = request.GET['end_date']
    try:
        analytics = initialize_analyticsreporting()
        number_of_users = get_report_users(analytics, start_date, end_date)

        RESULT_JSON['users'] = int(number_of_users)
        RESULT_JSON['status'] = 200

    except Exception as e:
        errors.append(str(e))
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = errors

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


@require_GET
def activeCustomerBreakdown(request):
    RESULT_JSON = {
        "status": 200,
        "customer_breakdown": processActiveCustomerBreakdown()
    }
    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


@require_GET
def userChurnRate(request):
    try:
        RESULT_JSON = {
            "status": 200,
            "churn_rate_breakdown": getChurnRate()
        }
    except Exception as e:
        RESULT_JSON = {
            "status": 500,
            "error_message": str(e)
        }
    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


@require_GET
def newSignups(request):
    RESULT_JSON = {}
    errors = []

    try:
        count = getNumberOfNewSignups()

        RESULT_JSON['status'] = 200
        RESULT_JSON['count'] = count

    except Exception as e:
        errors.append(str(e))
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = errors

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


@require_GET
def lifetimeValue(request):
    RESULT_JSON = {}
    errors = []
    if 'date' in request.GET.keys():
        dateStr = request.GET['date']
        date = datetime.strptime(dateStr, '%d-%m-%Y').date()
    else:
        date = datetime.now()

    try:
        lifetimeValue = getLifeTimeValue(date.month, date.year)

        RESULT_JSON['status'] = 200
        RESULT_JSON['lifetime_value'] = lifetimeValue

    except Exception as e:
        errors.append(str(e))
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = errors

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


@adminOnly
@require_GET
def revenue(request):

    start_date_str = request.GET['start_date']
    end_date_str = request.GET['end_date']

    start_date = datetime.strptime(start_date_str, '%d-%m-%Y').date()
    end_date = datetime.strptime(end_date_str, "%d-%m-%Y").date()

    RESULT_JSON = processGetRevenue(start_date, end_date)

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


class ActiveCustomersByMonth(BaseApiView):

    group_required = ('admin', )

    def get_customers_by_month(self):
        first_order_date = Order.objects.earliest('id').date.date()
        from_date = datetime(
            first_order_date.year, first_order_date.month, 1, tzinfo=CTZ)
        date_by_months = list(rrule.rrule(
            freq=rrule.MONTHLY, dtstart=from_date.date(),
            until=datetime.now(tz=CTZ).date()))
        result = []

        for date in date_by_months:
            customers = Customer.objects.filter(
                orders__date__range=(date, date + relativedelta(months=+1)),
                orders__status=Order.SHIPPED).distinct()
            subscribers = Customer.objects.filter(
                orders__date__range=(date, date + relativedelta(months=+1)),
                orders__recurrent=True,
                orders__status=Order.SHIPPED).distinct()
            result.append({'date': date.isoformat(),
                           'customers': customers.count(),
                           'subscribers': subscribers.count()})
        return result

    def get(self, request, *args, **kwargs):
        return self.render_json_response(self.get_customers_by_month())


class DecayCustomersByMonth(BaseApiView):

    group_required = ('admin', )

    def get_active_customers_strict(self, customers_qs, date):
        """Strict sampling of active customers.

        Consider a customer is active if there was at least
        one shipped recurrent order in a month.
        """
        return customers_qs.filter(
            orders__date__range=(date, date + relativedelta(months=+1)),
            orders__recurrent=True,
            orders__status=Order.SHIPPED).distinct().count()

    def get_active_customers_not_strict(self, customers_qs, reg_date, from_date):
        """Not strict sampling of active customers.

        Consider a customer is active all the time between the first and
        last recurrent orders.
        """
        if from_date < reg_date:
            return 0
        elif from_date == reg_date:
            return customers_qs.filter(
                orders__shipping_date__range=(
                    from_date + relativedelta(months=+1),
                    datetime.now(tz=CTZ).date() + relativedelta(years=+1)),
                orders__recurrent=True,
                orders__status__in=[Order.ACTIVE, Order.PAUSED, Order.SHIPPED]
            ).distinct().count()
        return customers_qs.filter(
            orders__shipping_date__range=(
                from_date,
                datetime.now(tz=CTZ).date() + relativedelta(years=+1)),
            orders__recurrent=True,
            orders__status__in=[Order.ACTIVE, Order.PAUSED, Order.SHIPPED]
        ).distinct().count()

    def get_decay_customers_by_month(self):
        first_order_date = Order.objects.earliest('id').date.date()
        from_date = datetime(
            first_order_date.year, first_order_date.month, 1, tzinfo=CTZ)
        date_by_months = list(rrule.rrule(
            freq=rrule.MONTHLY, dtstart=from_date.date(),
            until=datetime.now(tz=CTZ).date()))
        result = []

        for date in date_by_months:
            # customers signed up in month
            customers = Customer.objects.filter(
                user__created_at__range=(date, date + relativedelta(months=+1)))
            res = []
            for _date in date_by_months:
                customers_strict = self.get_active_customers_strict(customers, _date)
                customers_not_strict = self.get_active_customers_not_strict(customers, date, _date)
                timestamp = int(dt_format(_date, 'U')) * 1000
                res.append({
                    'ts': timestamp,
                    'customers': customers_strict,
                    'customers_not_strict': customers_not_strict})
            result.append({'signed_up': date.isoformat(), 'data': res})
        return result

    def get(self, request, *args, **kwargs):
        return self.render_json_response(self.get_decay_customers_by_month())
