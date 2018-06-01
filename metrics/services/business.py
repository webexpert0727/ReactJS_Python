# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals

from dateutil.relativedelta import relativedelta

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from customers.models import Order

from .utils import (
    get_customers_signed_up_in_month,
    get_first_dates_of_months)


CTZ = timezone.get_current_timezone()


def revenue_churn_rate(from_date, time_delta, customers_cohort, **kwargs):
    """Return Revenue Churn Rate in $.

    $ of recurring revenue lost in period / $ of total revenue at begginning of period
    """
    next_period = from_date + time_delta
    revenue_at_start_period = Order.objects.filter(
        recurrent=True,
        customer__in=customers_cohort,
        shipping_date__range=(from_date, next_period),
        status__in=[Order.ACTIVE, Order.PAUSED, Order.SHIPPED],
    ).aggregate(total=Sum('amount'))['total']
    revenue_at_next_period = Order.objects.filter(
        recurrent=True,
        customer__in=customers_cohort,
        shipping_date__range=(next_period, next_period + time_delta),
        status__in=[Order.ACTIVE, Order.PAUSED, Order.SHIPPED],
    ).aggregate(total=Sum('amount'))['total']
    revenue_lost = revenue_at_start_period - revenue_at_next_period
    if revenue_lost < 0:
        return 0
    return float(revenue_lost / revenue_at_start_period)


def customer_churn_rate(from_date, time_delta, customers_cohort, **kwargs):
    """Return Customer Churn Rate in %.

    # of customers lost in period / # of total customers at begginning of period
    """
    next_period = from_date + time_delta
    customers_at_start_period = customers_cohort.filter(
        orders__recurrent=True,
        orders__shipping_date__range=(from_date, next_period),
        orders__status__in=[Order.ACTIVE, Order.PAUSED, Order.SHIPPED],
    ).distinct().count()
    cusomers_at_next_period = customers_cohort.filter(
        orders__recurrent=True,
        orders__shipping_date__range=(next_period, next_period + time_delta),
        orders__status__in=[Order.ACTIVE, Order.PAUSED, Order.SHIPPED],
    ).distinct().count()
    customers_lost = customers_at_start_period - cusomers_at_next_period
    if customers_lost < 0:
        return 0
    return customers_lost / customers_at_start_period


def customer_churn_rate_non_strict(from_date, time_delta, customers_cohort, **kwargs):
    """Like customer_churn_rate(), but non strict."""
    next_period = from_date + time_delta
    customers_at_start_period = customers_cohort.filter(
        orders__recurrent=True,
        orders__shipping_date__range=(from_date, next_period),
        orders__status__in=[Order.ACTIVE, Order.PAUSED, Order.SHIPPED],
    ).distinct().count()
    cusomers_at_next_period = customers_cohort.filter(
        orders__recurrent=True,
        orders__shipping_date__gte=next_period,
        orders__status__in=[Order.ACTIVE, Order.PAUSED, Order.SHIPPED],
    ).distinct().count()
    customers_lost = customers_at_start_period - cusomers_at_next_period
    if customers_lost < 0:
        return 0
    return customers_lost / customers_at_start_period


def customer_retention_rate(from_date, time_delta, customers_cohort, **kwargs):
    """Return Customer Retention Rate in %."""
    churn_rate = customer_churn_rate(from_date, time_delta, customers_cohort)
    return 1 - churn_rate


def customer_retention_rate_non_strict(from_date, time_delta, customers_cohort, **kwargs):
    """Return Customer Retention Rate in %. Non strict."""
    churn_rate = customer_churn_rate_non_strict(from_date, time_delta, customers_cohort)
    return 1 - churn_rate


def customer_cumulative_lifetime_value(from_date, time_delta, customers_cohort, **kwargs):
    """Return Cumulative Customer Lifetime Value.

    (Number of Orders) / (Number of Customers) * (Average Order Value)
    """
    signed_up = kwargs['signed_up']
    date_by_months = get_first_dates_of_months(
        from_date=signed_up, to_date=from_date)
    cumulative_value = 0
    for date in date_by_months:
        orders = Order.objects.filter(
            customer__in=customers_cohort,
            shipping_date__range=(date, date + time_delta),
            status__in=[Order.ACTIVE, Order.PAUSED, Order.SHIPPED],
        ).aggregate(
            avg_amount=Avg('amount'),
            num_orders=Count('id'),
            num_customers=Count('customer', distinct=True))
        num_orders = orders['num_orders']
        num_customers = orders['num_customers']
        average_order_value = orders['avg_amount']
        cumulative_value += num_orders / num_customers * average_order_value
    return cumulative_value


def customer_lifetime_value(from_date, time_delta, customers_cohort, **kwargs):
    """Return Customer Lifetime Value.

    - ARPU (average monthly recurring revenue per user)
    ARPU * (Average Retention Time)
    ARPU / (Churn Rate)

    TODO: https://www.slideshare.net/EricSeufert/ltv-spreadsheet-models-eric-seufert
    """
    signed_up = kwargs['signed_up']
    date_by_months = get_first_dates_of_months(
        from_date=signed_up, to_date=from_date)
    arpu_by_month = []
    for date in date_by_months:
        orders = Order.objects.filter(
            customer__in=customers_cohort,
            shipping_date__range=(date, date + time_delta),
            status__in=[Order.ACTIVE, Order.PAUSED, Order.SHIPPED],
        ).aggregate(
            sum_amount=Sum('amount'),
            num_customers=Count('customer', distinct=True))
        num_customers = orders['num_customers']
        sum_amount = orders['sum_amount']
        arpu = float(sum_amount / num_customers)
        arpu_by_month.append(arpu)
    arpu = sum(arpu_by_month) / len(arpu_by_month)

    churn_rate = [customer_churn_rate(date, time_delta, customers_cohort)
                  for date in date_by_months]
    avg_churn_rate = sum(churn_rate) / len(churn_rate)
    return arpu * (1 / avg_churn_rate)


def customer_acquisition_cost():
    """Customer acquisition cost (CAC).

    The estimated cost of gaining each new customer.
    For example, if we spend $1,000 on a campaign which directly
    results in 10 new customers, the CAC will be $100 per customer.
    Also be cool to segment CAC by source (organic, paid, email, social).

    Take all your acquisition marketing costs, then divide by
    the number of paying customers acquired over a period of time.
    """
    pass


def refunds():
    pass


def payments():
    pass


def failed_charges():
    pass


def coupons_redeemed():
    pass


def activation_rate():
    """How many visitors become customers.

    Or `Conversion rate` to customer.
    Conversion rate = (The number of leads / Visitors) x 100
    """
    pass


def reactivated_customers():
    pass


def net_revenue():
    pass


def oneoff_to_subscription_rate():
    """Trial-to-paid conversion rate."""
    pass


def monthly_unique_visitors():
    """Monthly unique visitors (UVs)."""
    pass


def monthly_recurring_revenue():
    """Monthly Recurring Revenue (MRR).

    Number of existing customers x Average Revenue per Customer
    """
    result = []
    date_by_months = get_first_dates_of_months()
    time_delta = relativedelta(months=+1)
    for date in date_by_months:
        orders = Order.objects.filter(
            shipping_date__range=(date, date + time_delta),
            status__in=[Order.ACTIVE, Order.PAUSED, Order.SHIPPED],
        ).aggregate(
            avg_amount=Avg('amount'),
            num_customers=Count('customer', distinct=True))
        value = round(orders['num_customers'] * (orders['avg_amount'] or 0), 2)
        result.append({'date': date, 'values': {'mrr': value}})
    return result


def new_monthly_recurring_revenue():
    """New Monthly Recurring Revenue (MRR)

    New MRR is the new monthly recurring revenue added in a given month.
    New MRR only refers to brand-new customers and does not include expansion
    revenue or upgrades to existing customer accounts.
    It is a great way to track new revenue growth on a consistent basis over time,
    as well as measure the amount and size of new customers that are added each month.
    """
    result = []
    date_by_months = get_first_dates_of_months()
    time_delta = relativedelta(months=+1)
    for date in date_by_months:
        customers = get_customers_signed_up_in_month(date)
        orders = Order.objects.filter(
            customer__in=customers,
            shipping_date__range=(date, date + time_delta),
            status__in=[Order.ACTIVE, Order.PAUSED, Order.SHIPPED],
        ).aggregate(
            avg_amount=Avg('amount'),
            num_customers=Count('customer', distinct=True))
        value = round(orders['num_customers'] * (orders['avg_amount'] or 0), 2)
        result.append({'date': date, 'values': {'new_mrr': value}})
    return result


def expansion_monthly_recurring_revenue():
    """Expansion Monthly Recurring Revenue (MRR)

    Additional MRR from existing customers
    (generally in the form of an upgrade).
    """
    result = []
    date_by_months = get_first_dates_of_months()
    time_delta = relativedelta(months=+1)
    for date in date_by_months:
        customers = get_customers_signed_up_in_month(date)
        orders = Order.objects.filter(
            ~Q(customer__in=customers),
            shipping_date__range=(date, date + time_delta),
            status__in=[Order.ACTIVE, Order.PAUSED, Order.SHIPPED],
        ).aggregate(
            avg_amount=Avg('amount'),
            num_customers=Count('customer', distinct=True))
        value = round(orders['num_customers'] * (orders['avg_amount'] or 0), 2)
        result.append({'date': date, 'values': {'expansion_mrr': value}})
    return result


def churn_monthly_recurring_revenue():
    """Churn Monthly Recurring Revenue (MRR)

    MRR lost from cancellations.
    """
    result = []
    date_by_months = get_first_dates_of_months()
    time_delta = relativedelta(months=+1)
    for date in date_by_months:
        orders = Order.objects.filter(
            shipping_date__range=(date, date + time_delta),
            status=Order.CANCELED,
        ).aggregate(
            avg_amount=Avg('amount'),
            num_customers=Count('customer', distinct=True))
        value = - round(orders['num_customers'] * (orders['avg_amount'] or 0), 2)
        result.append({'date': date, 'values': {'churn_mrr': value}})
    return result


def net_new_monthly_recurring_revenue():
    """Net New Monthly Recurring Revenue (MRR)

    Net New MRR = New MRR + Expansion MRR - Churn MRR

    If churn more MRR than we get from New or Expansion MRR, we end up losing MRR
    that month… which would make as sad. Very, very sad.
    """
    result = []
    date_by_months = get_first_dates_of_months()
    new_mrr = new_monthly_recurring_revenue()
    expansion_mrr = expansion_monthly_recurring_revenue()
    churn_mrr = churn_monthly_recurring_revenue()
    for i, date in enumerate(date_by_months):
        _new_mrr = new_mrr[i]['values']['new_mrr']
        _expansion_mrr = expansion_mrr[i]['values']['expansion_mrr']
        _churn_mrr = churn_mrr[i]['values']['churn_mrr']
        value = (_new_mrr + _expansion_mrr - _churn_mrr)
        result.append({'date': date, 'values': {'net_mrr': value}})
    return result
