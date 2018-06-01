# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import calendar
from datetime import datetime, timedelta

from dateutil import rrule
from dateutil.relativedelta import relativedelta

from django.db.models import Count, Sum
from django.utils import timezone

from customers.models import Customer, Order

from .. import intercom_api
from .. import utils
from ..models import ChurnRateData


CTZ = timezone.get_current_timezone()


def processCoffeePerformance(start_date_str, end_date_str):
    start_date = datetime.strptime(start_date_str, '%d-%m-%Y').date()
    end_date = datetime.strptime(end_date_str, '%d-%m-%Y').date()

    # due to query issue, have to add one day to the end date in order to get results that have this particular end date
    end_date = end_date + timedelta(days=1)

    # retrieve all SHIPPED orders within specified date range
    orders_set = Order.objects.filter(shipping_date__gte=start_date,
                                      shipping_date__lt=end_date,
                                      status='SH')

    # iterate through orders, sort by coffee performance
    coffee_performance = {}

    for order in orders_set:
        coffee_name = order.coffee.name
        if coffee_name not in coffee_performance:
            coffee_performance[coffee_name] = 1
        else:
            coffee_performance[coffee_name] += 1

    l_coffee_performance = []

    for coffee_name in coffee_performance.keys():
        l_coffee_performance.append({
            "coffee": coffee_name,
            "count": coffee_performance[coffee_name]
        })

    return sorted(l_coffee_performance, key=lambda k: k['count'], reverse=True)


def processVoucherPerformance(start_date_str, end_date_str):
    start_date = datetime.strptime(start_date_str, '%d-%m-%Y').date()
    end_date = datetime.strptime(end_date_str, '%d-%m-%Y').date()

    # due to query issue, have to add one day to the end date in order to get results that have this particular end date
    end_date = end_date + timedelta(days=1)

    orders_set = Order.objects.filter(shipping_date__gte=start_date,
                                      shipping_date__lt=end_date,
                                      voucher__isnull=False)

    # iterate through orders, sort by voucher performance
    voucher_performance = {}

    for order in orders_set:
        voucher_name = order.voucher.name
        if voucher_name not in voucher_performance:
            voucher_performance[voucher_name] = 1
        else:
            voucher_performance[voucher_name] += 1

    l_voucher_performance = []

    for voucher_name in voucher_performance.keys():
        l_voucher_performance.append({
            "voucher_name": voucher_name,
            "count": voucher_performance[voucher_name]
        })

    return sorted(l_voucher_performance, key=lambda k: k['count'], reverse=True)


def processPercentageCustomersByAge():
    active_orders = Order.objects.filter(status='AC')

    active_customers = []

    for order in active_orders:
        customer = order.customer
        if customer not in active_customers:
            active_customers.append(customer)

    number_of_active_customers = len(active_customers)

    customer_numbers_by_age = {
        '< 1 month': 0,
        '1 - 3 months': 0,
        '3 - 6 months': 0,
        '6 - 12 months': 0,
        '> 12 months': 0
    }

    for customer in active_customers:
        customer_orders = Order.objects.filter(customer=customer)
        first_order = customer_orders.earliest('shipping_date')
        latest_order = customer_orders.latest('shipping_date')

        first_order_shipping_date = first_order.shipping_date
        latest_order_shipping_date = latest_order.shipping_date

        month_delta = utils.diff_month(latest_order_shipping_date, first_order_shipping_date)

        if month_delta < 1:
            customer_numbers_by_age['< 1 month'] += 1
        elif month_delta < 3:
            customer_numbers_by_age['1 - 3 months'] += 1
        elif month_delta < 6:
            customer_numbers_by_age['3 - 6 months'] += 1
        elif month_delta < 12:
            customer_numbers_by_age['6 - 12 months'] += 1
        else:
            customer_numbers_by_age['> 12 months'] += 1

    l_customer_percetage_by_age = []
    for type in customer_numbers_by_age.keys():
        l_customer_percetage_by_age.append({
            "type": type,
            "count": round(float(customer_numbers_by_age[type]) / number_of_active_customers * 100, 2)
        })

    return l_customer_percetage_by_age


def processActiveCustomerBreakdown():
    now = timezone.now()

    active = Customer.objects.active().count()
    inactive_one_month = (
        Customer.objects.inactive(from_date=now + timedelta(days=-30)).count())
    inactive_three_month = (
        Customer.objects.inactive(from_date=now + timedelta(days=-30 * 3)).count())
    inactive_six_month = (
        Customer.objects.inactive(from_date=now + timedelta(days=-30 * 6)).count())

    total = float(sum([
        active, inactive_one_month, inactive_three_month, inactive_six_month]))
    return {
        'active': active / total * 100,
        'inactive_one_month': inactive_one_month / total * 100,
        'inactive_three_month': inactive_three_month / total * 100,
        'inactive_six_month': inactive_six_month / total * 100,
    }


def calculateChurnRate(month, year):
    date_key = datetime(year, month, 1, 0, 0).strftime('%b-%Y')
    data, created = ChurnRateData.objects.get_or_create(month_year=date_key,
                                                        defaults={'proportion_churned': 0})
    if created or (month == datetime.now().month and year == datetime.now().year):
        current_month = datetime(year, month, 1, tzinfo=CTZ)
        next_month = current_month + relativedelta(months=+1)
        # retrieve active customers that month (who has an order shipped in that month)
        customers_for_month_year = Customer.objects.filter(
            orders__shipping_date__range=(current_month, next_month)
        ).distinct().values_list('id', flat=True)

        # how many of those customers have shipped orders in the next month?
        if month == datetime.now().month and year == datetime.now().year:
            customers_for_next_month_year = Customer.objects.filter(
                orders__shipping_date__gte=current_month,
                orders__status='AC',
            ).distinct().values_list('id', flat=True)
        else:
            customers_for_next_month_year = Customer.objects.filter(
                orders__shipping_date__range=(
                    next_month, next_month + relativedelta(months=+1))
            ).distinct().values_list('id', flat=True)
        attrition = len(set(customers_for_month_year) -
                        set(customers_for_next_month_year))
        if len(customers_for_month_year) == 0:
            data.proportion_churned = 0
        else:
            data.proportion_churned = float(attrition) / len(customers_for_month_year)
        data.save()
    return float(data.proportion_churned)


def getChurnRate():
    '''
        retrieves churn rate for past year
    '''
    month_years = utils.generate_month_year_tuples(12)

    monthly_attrition = []

    for (month, year) in month_years:
        date_key = datetime(year, month, 1, 0, 0).strftime('%b-%Y')
        attrition = calculateChurnRate(month, year)
        monthly_attrition.append(
            {
            'month': date_key,
            'rate': attrition
            }
        )

    return monthly_attrition
    # number of customers who quit / total new customers in the month


def getNumberOfNewSignups():
    now = timezone.now()
    # retrieve all orders that created accounts yesterday
    # and get very first order created
    orders = (
        Order.objects
        .filter(
            customer__user__created_at__gte=now - timedelta(days=1),
            customer__user__created_at__lt=now,
            status=Order.ACTIVE)
        .distinct('customer')
        .order_by('customer', 'date')
    )
    result = {'recurring': 0, 'one_off': 0}
    for order in orders:
        if order.recurrent:
            result['recurring'] += 1
        else:
            result['one_off'] += 1
    return result


def getLifeTimeValue(month, year):
    # average value / churn rate
    # get all orders for the month
    # get total revenue
    orders = (
        Order.objects
        .filter(
            shipping_date__month=month,
            shipping_date__year=year,
            status__in=['AC', 'SH', 'PA'])
        .aggregate(
            total=Sum('amount'),
            num_customers=Count('customer', distinct=True))
    )
    average_revenue = (orders['total'] / orders['num_customers']
                       if orders['num_customers'] else 0)
    # get churn rate for month
    churn_rate = calculateChurnRate(month, year)
    if churn_rate == 0:
        return 0
    return average_revenue / churn_rate


def processGetRevenue(start_date, end_date):

    # check whether end date lesser than start date
    if end_date < start_date:
        return {'status': 500,
                'error_message': "End date cannot be lesser than start date"}

    result = []
    today_date = datetime.now().date()

    # calculate revenue from past months
    for dt in rrule.rrule(rrule.MONTHLY, dtstart=start_date, until=end_date):
        date = dt.date()
        if date.month == today_date.month and date.year == today_date.year:
            continue

        first_date_of_month = datetime(date.year, date.month, 1).date()
        last_date_of_month = datetime(
            date.year, date.month,
            calendar.monthrange(date.year, date.month)[1]).date()
        query_end_date = last_date_of_month + timedelta(days=1)

        orders = Order.objects.filter(shipping_date__gte=first_date_of_month,
                                      shipping_date__lt=query_end_date)\
                              .exclude(status__in=['CA', 'DE'])

        revenue = 0

        for order in orders:
            revenue += order.amount

        result.append(
            {
                'date': '%s-%s' % (date.month, date.year),
                'revenue': float(revenue)
            }
        )

    # set start date to first day of start date's month
    # and set end date to last day of end date's month
    start_date_first_day = datetime(start_date.year, start_date.month, 1).date()
    end_date_last_day = datetime(
        end_date.year, end_date.month,
        calendar.monthrange(end_date.year, end_date.month)[1]).date()

    # only calculate total expected revenue and actual revenue for
    # current month if today's date is between dates specified
    if today_date > start_date_first_day and today_date < end_date_last_day:
        first_date_of_current_month = datetime(
            today_date.year, today_date.month, 1).date()
        last_date_of_current_month = datetime(
            today_date.year, today_date.month,
            calendar.monthrange(today_date.year, today_date.month)[1]).date()
        query_end_date = (
            last_date_of_current_month + timedelta(days=1))

        current_month_orders = (
            Order.objects
            .filter(shipping_date__gte=first_date_of_current_month,
                    shipping_date__lt=query_end_date)
            .exclude(status__in=['CA', 'DE']))
        revenue = 0
        realised_revenue = 0

        for order in current_month_orders:
            if order.status == 'SH':
                realised_revenue += order.amount

            revenue += order.amount

        result.append(
            {
                'date': '%s-%s' % (today_date.month, today_date.year),
                'revenue': float(revenue),
                'realised_revenue': float(realised_revenue)
            }
        )

    return {
        'status': 200,
        'months_revenue': result
    }
