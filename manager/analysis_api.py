# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import calendar
import datetime

from dateutil import relativedelta, rrule

from django.core.exceptions import ObjectDoesNotExist

from customers.models import Order

from . import stochasticknapsack
from .models import CustomerCluster, Recommendation, ReportCard
from .utils import (
    countOrdersByDate, getNumberOfActiveCustomersByDate,
    getNumberOfChurnCustomersByDate, getNumberOfNewSignupsByDate)


def processUpdateReportCard(report_id, facebook_advertising_cost, blog_posts, email_campaigns, adwords_cost, roadshows, new_coffees):

    check_negative = []

    try:
        report_id = int(report_id)
        facebook_advertising_cost = float(facebook_advertising_cost)
        adwords_cost = float(adwords_cost)
        new_coffees = int(new_coffees)
        email_campaigns = int(email_campaigns)
        roadshows = int(roadshows)
        blog_posts = int(blog_posts)

    except ValueError as e:
        #input validation
        return {
            'status': 500,
            'error_message': str(e)
        }

    check_negative.append(report_id)
    check_negative.append(facebook_advertising_cost)
    check_negative.append(adwords_cost)
    check_negative.append(new_coffees)
    check_negative.append(email_campaigns)
    check_negative.append(roadshows)
    check_negative.append(blog_posts)

    #check for negativity
    for number in check_negative:
        if number < 0:
            return {
                'status': 500,
                'error_message': 'Numbers input cannot be negative'
            }

    try:
        #update report card
        report_card = ReportCard.objects.get(id=report_id)
        actions = report_card.actions

        actions['facebook_advertising_cost'] = facebook_advertising_cost
        actions['blog_posts'] = blog_posts
        actions['email_campaigns'] = email_campaigns
        actions['adwords_cost'] = adwords_cost
        actions['roadshows'] = roadshows
        actions['new_coffees'] = new_coffees

        #calculate deviations from recommendation

        try:
            recommendation = Recommendation.objects.get(date__month=report_card.date.month, date__year=report_card.date.year)
            # deviation = root(E[(actual - predicted / predicted)^2])
            total_deviation = 0.0

            total_deviation += ((
                                    float(facebook_advertising_cost) - recommendation.facebook_advertising_cost) / recommendation.facebook_advertising_cost) ** 2
            total_deviation += ((
                                    float(blog_posts) - recommendation.blog_posts) / recommendation.blog_posts) ** 2
            total_deviation += ((
                                    float(email_campaigns) - recommendation.email_campaigns) / recommendation.email_campaigns) ** 2
            total_deviation += ((
                                    float(adwords_cost) - recommendation.adwords_cost) / recommendation.adwords_cost) ** 2
            total_deviation += ((
                                    float(roadshows) - recommendation.roadshows) / recommendation.roadshows) ** 2
            total_deviation += ((
                                    float(new_coffees) - recommendation.new_coffees) / recommendation.new_coffees) ** 2

            deviation = (total_deviation / 6) ** 0.5

            report_card.deviation = deviation

        except:
            report_card.deviation = 0

        report_card.save()

    except ObjectDoesNotExist:
        return {
            'status': 500,
            'error_message': 'Report with ID %s does not exist' % report_id
        }
    except Exception as e:
        return {
            'status': 500,
            'error_message': str(e)
        }

    return {
        'status' : 200,
        'message' : 'Report Card has been successfully updated!'
    }


def processGetReportCard(start_date, end_date):
    """
    Get report card for every month according to the specified date range
    If report card is not found for that month,
     If the input month is less than the current month,
     create a new report card with actions set to 0 value
     else return an empty report card for that month
    """
    stochasticknapsack.bootstrap()

    # check whether end date lesser than start date
    if end_date < start_date:
        return {
            'status': 500,
            'error_message': "End date cannot be lesser than start date"
        }

    reports = []
    today_date = datetime.datetime.now().date()

    try:
        for dt in rrule.rrule(rrule.MONTHLY,dtstart=start_date,until=end_date):
            date = dt.date()
            query_start_date = datetime.date(date.year, date.month, 1)
            query_end_date = datetime.date(date.year, date.month, calendar.monthrange(date.year, date.month)[1])

            # previous month's dates
            previous_month_start_date = query_start_date - relativedelta.relativedelta(months=1)
            previous_month_end_date = query_end_date - relativedelta.relativedelta(months=1)
            previous_month_end_date = datetime.date(previous_month_end_date.year, previous_month_end_date.month,
                                                    calendar.monthrange(previous_month_end_date.year,
                                                                        previous_month_end_date.month)[1])

            try:
                report_card = ReportCard.objects.filter(
                    date__month=date.month, date__year=date.year).latest('date')
            except ObjectDoesNotExist:
                if date.month < today_date.month:
                    try:
                        recommendation = Recommendation.objects.get(date__month=date.month, date__year=date.year)
                        expected_demand = recommendation.expected_demand
                    except:
                        expected_demand = 0

                    target_month = datetime.date(date.year, date.month, 1)
                    t_1 = (target_month - datetime.timedelta(days=1)).replace(day=1)
                    denominator = Order.objects.filter(
                        shipping_date__month=t_1.month, shipping_date__year=t_1.year).count()

                    if denominator == 0:
                        percentageChangeDemand = 0
                    else:
                        percentageChangeDemand = (float(Order.objects.filter(
                            shipping_date__month=date.month, shipping_date__year=date.year).count()) / Order.objects.filter(
                            shipping_date__month=t_1.month, shipping_date__year=t_1.year).count() - 1) * 100
                    report_card = ReportCard(
                                    date=datetime.date(date.year, date.month, 1),
                                    active_customers=getNumberOfActiveCustomersByDate(query_start_date, query_end_date),
                                    orders=countOrdersByDate(query_start_date, query_end_date),
                                    churn=getNumberOfChurnCustomersByDate(query_start_date, query_end_date),
                                    new_signups=getNumberOfNewSignupsByDate(query_start_date, query_end_date),
                                    actions={
                                         'facebook_advertising_cost' : 0.00,
                                         'blog_posts' : 0,
                                         'email_campaigns' : 0,
                                         'adwords_cost' : 0.00,
                                         'roadshows': 0,
                                         'new_coffees' : 0
                                    },
                                    percentage_changes={},
                                    expected_demand=expected_demand,
                                    demand_actualising=percentageChangeDemand,
                                    deviation=0.0
                                 )
                    report_card.save()

                    report_card.percentage_changes = getPercentageChange(previous_month_start_date, previous_month_end_date, report_card)

                    report_card.save()

                else:
                    reports.append(
                        {
                            'date': '%s-%s' % (date.month, date.year),
                            'report_card': {
                                'report_id' : 0,
                                'active_customers': 0,
                                'orders': 0,
                                'churn': 0,
                                'new_signups': 0,
                                'percentage_active_customers' : 0,
                                'percentage_orders' : 0,
                                'percentage_churn' : 0,
                                'percentage_new_signups' : 0,
                                'actions' : {},
                                'percentage_changes' : {},
                                'expected_demand' : 0.0,
                                'demand_actualising' : 0.0,
                                'deviation' : 0.0
                            }
                        }
                    )
                    continue
            reports.append(
                {
                    'date': '%s-%s' % (date.month, date.year),
                    'report_card' : {
                        'report_id' : report_card.id,
                        'active_customers' : report_card.active_customers,
                        'orders' : report_card.orders,
                        'churn' : report_card.churn,
                        'new_signups' : report_card.new_signups,
                        'percentage_changes' : report_card.percentage_changes,
                        'actions' : report_card.actions,
                        'expected_demand': float(report_card.expected_demand),
                        'demand_actualising': float(report_card.demand_actualising),
                        'deviation': float(report_card.deviation)
                    }
                }
            )
    except Exception as e:
        return {
            'status': 500,
            'error_message': str(e)
        }

    return {
        'status' : 200,
        'reports' : reports
    }


def processSaveRecommendation(facebook_advertising_cost, adwords_cost, new_coffees, email_campaigns, roadshows, blog_posts, expected_demand, demand_actualising):

    check_negative = []

    try:
        facebook_advertising_cost = float(facebook_advertising_cost)
        adwords_cost = float(adwords_cost)
        new_coffees = int(new_coffees)
        email_campaigns = int(email_campaigns)
        roadshows = int(roadshows)
        blog_posts = int(blog_posts)
        expected_demand = float(expected_demand)
        demand_actualising = float(demand_actualising)

    except ValueError as e:
        #input validation
        return {
            'status': 500,
            'error_message': str(e)
        }

    check_negative.append(facebook_advertising_cost)
    check_negative.append(adwords_cost)
    check_negative.append(new_coffees)
    check_negative.append(email_campaigns)
    check_negative.append(roadshows)
    check_negative.append(blog_posts)
    check_negative.append(expected_demand)
    check_negative.append(demand_actualising)

    #check for negativity
    for number in check_negative:
        if number < 0:
            return {
                'status': 500,
                'error_message': 'Numbers input cannot be negative'
            }



    try:
        recommendation = Recommendation(facebook_advertising_cost=facebook_advertising_cost,
                                        adwords_cost=adwords_cost,
                                        new_coffees=new_coffees,
                                        email_campaigns=email_campaigns,
                                        roadshows=roadshows,
                                        blog_posts=blog_posts,
                                        expected_demand=expected_demand,
                                        demand_actualising=demand_actualising)

        recommendation.save()

    except Exception as e:
        return {
            'status': 500,
            'error_message': str(e)
        }

    return {
        'status' : 200,
        'message' : 'Recommendation has been successfully saved!'
    }


def processGetRecommendation():
    # get recommendation from db if it exists
    return stochasticknapsack.getValues(datetime.datetime.today().month, datetime.datetime.today().year)


def processGetCustomerSegments():

    clusters = []

    try:
        customer_clusters = CustomerCluster.objects.all()
        for cluster in customer_clusters:
            clusters.append(
                {
                    'cluster_name' : cluster.cluster_name,
                    'cluster_number' : cluster.cluster_number,
                    'cluster_description' : cluster.cluster_description,
                    'mean_orders' : float(cluster.mean_orders),
                    'mean_ratio_amount_time' : float(cluster.mean_ratio_amount_time),
                    'mean_vouchers_used' : float(cluster.mean_vouchers_used),
                    'mean_interval' : float(cluster.mean_interval),
                    'mean_total_spending' : float(cluster.mean_total_spending),
                    'mean_one_off_orders' : float(cluster.mean_one_off_orders),
                    'customers' : cluster.customers['customers'],
                    'percentage_brew_methods' : cluster.percentage_brew_methods,
                    'cluster_revenue' : float(cluster.cluster_revenue)
                }
            )

    except Exception as e:
        return {
            'status': 500,
            'error_message': str(e)
        }

    return {
        'status' : 200,
        'clusters' : clusters
    }


def getPercentageChange(previous_month_start_date, previous_month_end_date, report_card):

    #query for previous month's report card
    previous_month_report_card = ReportCard.objects.filter(date__month=previous_month_start_date.month).latest('date')

    # retrieve statistics from previous month
    previous_month_active_customers = getNumberOfActiveCustomersByDate(previous_month_start_date, previous_month_end_date)
    previous_month_orders = countOrdersByDate(previous_month_start_date, previous_month_end_date)
    previous_month_new_signups = getNumberOfNewSignupsByDate(previous_month_start_date, previous_month_end_date)
    previous_month_churn = getNumberOfChurnCustomersByDate(previous_month_start_date, previous_month_end_date)

    previous_month_actions = previous_month_report_card.actions
    previous_month_facebook_advertising_cost = previous_month_actions['facebook_advertising_cost']
    previous_month_blog_posts = previous_month_actions['blog_posts']
    previous_month_adwords_cost = previous_month_actions['adwords_cost']
    previous_month_email_campaigns = previous_month_actions['email_campaigns']
    previous_month_roadshows = previous_month_actions['roadshows']
    previous_month_new_coffees = previous_month_actions['new_coffees']

    if previous_month_active_customers != 0:
        percentage_active_customers = (float(report_card.active_customers) - previous_month_active_customers) / previous_month_active_customers * 100.0
    else:
        percentage_active_customers = 0.0

    if previous_month_orders != 0:
        percentage_orders = (float(report_card.orders) - previous_month_orders) / previous_month_orders * 100.0
    else:
        percentage_orders = 0.0

    if previous_month_new_signups != 0:
        percentage_new_signups = (float(report_card.new_signups) - previous_month_new_signups) / previous_month_new_signups * 100.0
    else:
        percentage_new_signups = 0.0

    if previous_month_churn != 0:
        percentage_churn = (float(report_card.churn) - previous_month_churn) / previous_month_churn * 100.0
    else:
        percentage_churn = 0.0

    if previous_month_facebook_advertising_cost != 0:
        percentage_facebook_advertising_cost = (float(report_card.actions['facebook_advertising_cost']) - previous_month_facebook_advertising_cost) / previous_month_facebook_advertising_cost * 100.0
    else:
        percentage_facebook_advertising_cost = 0.0

    if previous_month_blog_posts != 0:
        percentage_blog_posts = (float(report_card.actions['blog_posts']) - previous_month_blog_posts) / previous_month_blog_posts * 100.0
    else:
        percentage_blog_posts = 0.0

    if previous_month_adwords_cost != 0:
        percentage_adwords_cost = (float(report_card.actions['adwords_cost']) - previous_month_adwords_cost) / previous_month_adwords_cost * 100.0
    else:
        percentage_adwords_cost = 0.0

    if previous_month_email_campaigns != 0:
        percentage_email_campaigns = (float(report_card.actions['email_campaigns']) - previous_month_email_campaigns) / previous_month_email_campaigns * 100.0
    else:
        percentage_email_campaigns = 0.0

    if previous_month_roadshows != 0:
        percentage_roadshows = (float(report_card.actions['roadshows']) - previous_month_roadshows) / previous_month_roadshows * 100.0
    else:
        percentage_roadshows = 0.0

    if previous_month_new_coffees != 0:
        percentage_new_coffees = (float(report_card.actions['new_coffees']) - previous_month_new_coffees) / previous_month_new_coffees * 100.0
    else:
        percentage_new_coffees = 0.0

    return {
        'percentage_active_customers' : round(percentage_active_customers, 2),
        'percentage_orders' : round(percentage_orders, 2),
        'percentage_new_signups' : round(percentage_new_signups, 2),
        'percentage_churn' : round(percentage_churn, 2),
        'percentage_facebook_advertising_cost' : round(percentage_facebook_advertising_cost, 2),
        'percentage_blog_posts' : round(percentage_blog_posts, 2),
        'percentage_adwords_cost' : round(percentage_adwords_cost, 2),
        'percentage_email_campaigns' : round(percentage_email_campaigns, 2),
        'percentage_roadshows' : round(percentage_roadshows, 2),
        'percentage_new_coffees' : round(percentage_new_coffees, 2)
    }


