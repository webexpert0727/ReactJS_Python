import datetime
import random
import math
from copy import deepcopy

import numpy
import statsmodels.api as sm

from scipy.optimize import differential_evolution
from pandas import DataFrame
from patsy.highlevel import dmatrices

from customers.models import Order

# minimum expected percentage change
from manager.models import Recommendation, ReportCard
from manager.utils import getNumberOfActiveCustomersByDate, countOrdersByDate, getNumberOfChurnCustomersByDate, \
    getNumberOfNewSignupsByDate

MU = 0.05

COST = [
    0.0,
    1.0,
    1.0,
    20.0,
    60.0,
    4.0,
    400.0
]
x0_bounds = (0, 0)
x1_6_bounds = (0, None)

HISTORICAL_DATA = {
    "mu": [0.132939439, 0.148430874, 0.238445378, 0.15114873, 0.020987654, 0.106557377, 0.686635945, 0.085],
    "num_active_cus_1m": [202, 177, 139, 124, 130, 111, 82, 61],
    "google": [319.57, 518.39, 512.53, 229.18, 90.17, 167.32, 134.19, 5.68],
    "facebook": [15, 70, 0, 0, 0, 27, 0, 0],
    "new_coffees": [1, 2, 1, 3, 2, 2, 1, 1],
    "wordpress": [5, 7, 1, 3, 2, 8, 4, 0],
    "email": [10, 7, 8, 6, 8, 11, 8, 6],
    "roadshow": [8, 5, 0, 0, 0, 0, 0, 0],
}


def calculateBudget(old_budget, month, year):
    # calculates budget as a weighted avg of customers of past 3 months
    # 3/6 * previous month (t-1) orders + 2/6 of previous month's order (t-2) + 1/6 of 2 months ago order (t-3)
    # denominator 3/6 * t-2 orders * 2/6 * t-3 orders + 1/6 * t-4 orders

    # create a date object for the 3 months
    this_month = datetime.date(year, month, 1)
    t_1 = (this_month - datetime.timedelta(days=1)).replace(day=1)
    t_2 = (t_1 - datetime.timedelta(days=1)).replace(day=1)
    t_3 = (t_2 - datetime.timedelta(days=1)).replace(day=1)
    t_4 = (t_3 - datetime.timedelta(days=1)).replace(day=1)

    t_1_orders = Order.objects.filter(shipping_date__gte=t_1, shipping_date__lt=this_month).count()
    t_2_orders = Order.objects.filter(shipping_date__gte=t_2, shipping_date__lt=t_1).count()
    t_3_orders = Order.objects.filter(shipping_date__gte=t_3, shipping_date__lt=t_2).count()
    t_4_orders = Order.objects.filter(shipping_date__gte=t_4, shipping_date__lt=t_3).count()

    new_budget = old_budget * ((0.5 * t_1_orders + 2.0 / 6 * t_2_orders + 1.0 / 6 * t_3_orders) / (
        0.5 * t_2_orders + 2.0 / 6 * t_3_orders + 1.0 / 6 * t_4_orders))

    return new_budget


def regress(new_data=HISTORICAL_DATA):
    data = DataFrame.from_dict(new_data)

    y, X = dmatrices('mu ~ wordpress + roadshow + email + facebook + google + new_coffees', data=data,
                     return_type='dataframe')
    model = sm.OLS(y, X)
    res = model.fit()

    return res.conf_int()


def generate_mc_samples(ci, sample_count=1000):
    # we are going to assume that each of our bi will be positive in nature, so we only take the positive portion
    # returns a list of 200 sample vectors of b0...b6
    samples = []

    min_b0 = max(ci[0]['Intercept'], 0)
    max_b0 = ci[1]['Intercept']
    min_b1 = max(ci[0]['google'], 0)
    max_b1 = ci[1]['google']
    min_b2 = max(ci[0]['facebook'], 0)
    max_b2 = ci[1]['facebook']
    min_b3 = max(ci[0]['new_coffees'], 0)
    max_b3 = ci[1]['new_coffees']
    min_b4 = max(ci[0]['wordpress'], 0)
    max_b4 = ci[1]['wordpress']
    min_b5 = max(ci[0]['email'], 0)
    max_b5 = ci[1]['email']
    min_b6 = max(ci[0]['roadshow'], 0)
    max_b6 = ci[1]['roadshow']

    for i in range(sample_count):
        sample = []
        sample.append(random.uniform(min_b0, max_b0))
        sample.append(random.uniform(min_b1, max_b1))
        sample.append(random.uniform(min_b2, max_b2))
        sample.append(random.uniform(min_b3, max_b3))
        sample.append(random.uniform(min_b4, max_b4))
        sample.append(random.uniform(min_b5, max_b5))
        sample.append(random.uniform(min_b6, max_b6))
        samples.append(sample)

    return samples


def indicator(input, mu):
    if mu < input :
        return 0
    else:
        return 1


# this is our objective function
def F(x, samples, budget, B):
    # x is our weights
    if numpy.dot(x, B) <= 0:
        return len(samples) + 50
    if numpy.dot(x, COST) > budget or any(t <= 0 for t in x[1:]):
        return len(samples) + 1
    result = 0
    for sample in samples:
        new_mu = numpy.dot(x, sample)
        result += indicator(new_mu, MU)
    return result


def solve(budget, new_data=HISTORICAL_DATA, is_random=False):

    bounds = [
        (0, 0),
        (max(min(new_data['google'] - numpy.std(new_data['google'])),0),
         max(new_data['google'] + numpy.std(new_data['google']))),
        (max(min(new_data['facebook'] - numpy.std(new_data['facebook'])),0),
         max(new_data['facebook'] + numpy.std(new_data['facebook']))),
        (max(min(new_data['new_coffees'] - numpy.std(new_data['new_coffees'])),0),
         max(new_data['new_coffees'] + numpy.std(new_data['new_coffees']))),
        (max(min(new_data['wordpress'] - numpy.std(new_data['wordpress'])),0),
         max(new_data['wordpress'] + numpy.std(new_data['wordpress']))),
        (max(min(new_data['email'] - numpy.std(new_data['email'])),0),
         max(new_data['email'] + numpy.std(new_data['email']))),
        (max(min(new_data['roadshow'] - numpy.std(new_data['roadshow'])),0),
         max(new_data['roadshow'] + numpy.std(new_data['roadshow'])))
    ]
    if is_random:
        x = [random.uniform(bounds[0][0],bounds[0][1]),
                random.uniform(bounds[1][0],bounds[1][1]),
                random.uniform(bounds[2][0],bounds[2][1]),
                random.uniform(bounds[3][0],bounds[3][1]),
                random.uniform(bounds[4][0],bounds[4][1]),
                random.uniform(bounds[5][0],bounds[5][1]),
                random.uniform(bounds[6][0],bounds[6][1])]

        while numpy.dot(x, COST) > budget or any(t <= 0 for t in x[1:]):
            x = [random.uniform(bounds[0][0],bounds[0][1]),
                random.uniform(bounds[1][0],bounds[1][1]),
                random.uniform(bounds[2][0],bounds[2][1]),
                random.uniform(bounds[3][0],bounds[3][1]),
                random.uniform(bounds[4][0],bounds[4][1]),
                random.uniform(bounds[5][0],bounds[5][1]),
                random.uniform(bounds[6][0],bounds[6][1])]
        return x

    else:
        result = differential_evolution(F, bounds, args=(generate_mc_samples(regress(new_data)), budget, getB(new_data)),
                                    maxiter=100000, popsize=100)
        return result.x


def getB(new_data=HISTORICAL_DATA):
    data = DataFrame.from_dict(new_data)

    y, X = dmatrices('mu ~ wordpress + roadshow + email + facebook + google + new_coffees', data=data,
                     return_type='dataframe')
    model = sm.OLS(y, X)
    res = model.fit()

    return res.params


def getScaleFactor(new_data):
    # 8 / n^2 * 9 + 1
    original_size = len(HISTORICAL_DATA['mu'])
    new_size = len(new_data['mu'])

    return ((float(original_size) / (new_size)) ** 2) * 99 + 1


def getValues(month, year):
    this_month = datetime.date(year, month, 1)
    t_1 = (this_month - datetime.timedelta(days=1)).replace(day=1)

    try:
        demand_actualizing = ((float(Order.objects.filter(shipping_date__month=month, shipping_date__year=year).count()) /
                              Order.objects.filter(shipping_date__gte=t_1, shipping_date__lt=this_month).count()) - 1) * 100
    except:
        demand_actualizing = 0

    try:
        recommendation = Recommendation.objects.get(date__month=month, date__year=year)
        actions = {
                "facebook_advertising_cost": float(recommendation.facebook_advertising_cost),
                "blog_posts": int(recommendation.blog_posts),
                "adwords_cost": float(recommendation.adwords_cost),
                "email_campaigns": int(recommendation.email_campaigns),
                "roadshows": int(recommendation.roadshows),
                "new_coffees": int(recommendation.new_coffees)
            }

        expected_demand = recommendation.expected_demand

    except:
        budget = 1000
        new_data = {
            'mu':[],
            'google': [],
            'facebook': [],
            'new_coffees': [],
            'wordpress': [],
            'email': [],
            'roadshow': [],
            'num_active_cus_1m': [],
        }

        try:

            reports = ReportCard.objects.all()
            # bootstrap the data
            for report in reports:
                new_data['mu'].insert(0,float(report.demand_actualising)/100)
                new_data['google'].insert(0,report.actions['adwords_cost'])
                new_data['facebook'].insert(0,report.actions['facebook_advertising_cost'])
                new_data['new_coffees'].insert(0,report.actions['new_coffees'])
                new_data['wordpress'].insert(0,report.actions['blog_posts'])
                new_data['email'].insert(0,report.actions['email_campaigns'])
                new_data['roadshow'].insert(0,report.actions['roadshows'])
                new_data['num_active_cus_1m'].insert(0,report.active_customers)

        except:
            print "No reports found, using base data"

        try:
            # get previous month's recommendation
            recommendation = Recommendation.objects.get(date__gte=t_1, date__lte=this_month)
            budget = recommendation.budget

        except Exception as e:
            print e
            budget = 6000

        new_budget = calculateBudget(budget, month, year)

        actionsList = solve(new_budget, new_data)
        demand = numpy.dot(actionsList, getB(new_data))
        expected_demand = minimize(demand) * 100

        actions ={
                "facebook_advertising_cost": float(actionsList[2]),
                "blog_posts": int(math.ceil(actionsList[4])),
                "adwords_cost": float(actionsList[1]),
                "email_campaigns": math.ceil(actionsList[5]),
                "roadshows": math.ceil(actionsList[6]),
                "new_coffees": int(math.ceil(actionsList[3]))
            }


        r = Recommendation(facebook_advertising_cost=actionsList[2],
                           adwords_cost=actionsList[1],
                           new_coffees=math.ceil(actionsList[3]),
                           email_campaigns=math.ceil(actionsList[5]),
                           blog_posts=math.ceil(actionsList[4]),
                           roadshows=math.ceil(actionsList[6]),
                           budget=new_budget,
                           expected_demand=expected_demand,
                           demand_actualising=0)
        r.save()


    return {
        'status': 200,
        'actions': actions,
        'statistics': {
            'expected_demand': round(float(expected_demand), 2),
            'demand_actualising': float(max(0, demand_actualizing))
        }
    }


def minimize(demand):
    while demand > 0.3:
        demand /= 5
    return demand


def follow(d0, mu, month, year, actions, new_data, is_random):
    # follow and create a fake report card for the next month
    # we use the ito's process to draw a sample of expected demand

    e_dt = d0 * math.exp(mu)
    sigma = numpy.std(new_data['mu'])
    #print e_dt
    #print sigma
    var_dt = abs((d0**2) * math.exp(2 * mu) * (math.exp((sigma ** 2) * mu) - 1))
    #print var_dt
    drawn_demand = numpy.random.normal(e_dt, var_dt ** 0.5)

    if is_random:
        percentage_change = ((float(drawn_demand) - d0)/d0) * 100
    else:
        percentage_change = mu * 100
        drawn_demand = d0 * ((100+percentage_change)/100)

    report_card = ReportCard(
        date=datetime.date(year, month, 1),
        active_customers=0,
        orders=drawn_demand,
        churn=0,
        new_signups=0,
        actions={
            'facebook_advertising_cost': actions['facebook_advertising_cost'],
            'blog_posts': actions['blog_posts'],
            'email_campaigns': actions['email_campaigns'],
            'adwords_cost': actions['adwords_cost'],
            'roadshows': actions['roadshows'],
            'new_coffees': actions['new_coffees']
        },
        percentage_changes={},
        expected_demand=mu*100,
        demand_actualising=percentage_change,
        deviation=0.0
    )

    print "****** TRIAL for", report_card.date, "******"
    #print report_card.orders
    #print report_card.actions
    #print report_card.expected_demand
    #print report_card.demand_actualising
    #print [report_card.expected_demand, report_card.demand_actualising]
    report_card.save()



def trials(n=12, is_random=False):
    try:
        working_date = datetime.datetime.today().replace(day=1)
        working_date = (working_date - datetime.timedelta(days=1)).replace(day=1)
        for i in range(1, n+1):
            working_date = (working_date + datetime.timedelta(days=31)).replace(day=1)
            new_data = deepcopy(HISTORICAL_DATA)
            try:

                reports = ReportCard.objects.filter(date__gte=datetime.date(2016, 10, 1))
                # bootstrap the data
                for report in reports:
                    new_data['mu'].insert(0, float(report.demand_actualising)/100)
                    new_data['google'].insert(0, report.actions['adwords_cost'])
                    new_data['facebook'].insert(0, report.actions['facebook_advertising_cost'])
                    new_data['new_coffees'].insert(0, report.actions['new_coffees'])
                    new_data['wordpress'].insert(0, report.actions['blog_posts'])
                    new_data['email'].insert(0, report.actions['email_campaigns'])
                    new_data['roadshow'].insert(0, report.actions['roadshows'])
                    new_data['num_active_cus_1m'].insert(0, report.active_customers)

            except:
                print "No reports found, using base data"

            d0 = ReportCard.objects.latest('date').orders
            actionsList = solve(1000 * (1.05)**i, new_data, is_random=is_random)
            demand = numpy.dot(actionsList, getB(new_data))
            expected_demand = minimize(demand) * 100

            actions = {
                "facebook_advertising_cost": float(actionsList[2]),
                "blog_posts": int(math.ceil(actionsList[4])),
                "adwords_cost": float(actionsList[1]),
                "email_campaigns": math.ceil(actionsList[5]),
                "roadshows": math.ceil(actionsList[6]),
                "new_coffees": int(math.ceil(actionsList[3]))
            }

            r = Recommendation(facebook_advertising_cost=actionsList[2],
                               adwords_cost=actionsList[1],
                               new_coffees=math.ceil(actionsList[3]),
                               email_campaigns=math.ceil(actionsList[5]),
                               blog_posts=math.ceil(actionsList[4]),
                               roadshows=math.ceil(actionsList[6]),
                               budget=1000 * (1.05)**i,
                               expected_demand=expected_demand,
                               demand_actualising=0)
            #r.save()

            solution = {
                'status': 200,
                'actions': actions,
                'statistics': {
                    'expected_demand': round(float(expected_demand), 2),
                    'demand_actualising': float(max(0, 0))
                }
            }

            print "Expected percentage chagne in demand ",  solution['statistics']['expected_demand']/100
            # follow recommendation and get next data
            follow(d0, solution['statistics']['expected_demand']/100, working_date.month,
                   working_date.year, solution['actions'], new_data, is_random)
    except:
        pass
    print ">>>>>>>>>>>>>>>>>>>>>>>>>", ReportCard.objects.latest('date').date
    print ">>>>>>>>>>>>>>>>>>>>>>>>>" , ReportCard.objects.latest('date').orders
    date_delete_from_rc = datetime.date(2016, 10, 1)
    date_delete_from_re = datetime.date(2016, 11, 1)
    ReportCard.objects.filter(date__gte=date_delete_from_rc).delete()
    Recommendation.objects.filter(date__gte=date_delete_from_re).delete()


def bootstrap():
    # check if ReportCards have been populated
    start_date = datetime.date(2016, 1, 1)
    end_date = datetime.date(2016, 9, 30)

    num_reports = ReportCard.objects.filter(date__gte=start_date, date__lte=end_date).count()

    if num_reports < 8:
        # do the bootstrap
        ReportCard.objects.all().delete()

        for i in range(8):
            try:
                query_start_date = datetime.date(2016, 9 - i, 1)
                query_end_date = datetime.date(2016, 9 - i + 1, 1)

                t_1 = query_start_date - datetime.timedelta(days=1)

                denominator = Order.objects.filter(
                    shipping_date__month=t_1.month, shipping_date__year=t_1.year).count()
                if denominator == 0 :
                    percentageChangeDemand = 0
                else:
                    percentageChangeDemand = (float(Order.objects.filter(
                            shipping_date__month=query_start_date.month, shipping_date__year=query_start_date.year).count()) / Order.objects.filter(
                            shipping_date__month=t_1.month, shipping_date__year=t_1.year).count() - 1) * 100

                report_card = ReportCard(
                    date=datetime.date(2016, 9 - i, 1),
                    active_customers=getNumberOfActiveCustomersByDate(query_start_date, query_end_date),
                    orders=countOrdersByDate(query_start_date, query_end_date),
                    churn=getNumberOfChurnCustomersByDate(query_start_date, query_end_date),
                    new_signups=getNumberOfNewSignupsByDate(query_start_date, query_end_date),
                    actions={
                        'facebook_advertising_cost': HISTORICAL_DATA['facebook'][i],
                        'blog_posts': HISTORICAL_DATA['wordpress'][i],
                        'email_campaigns': HISTORICAL_DATA['email'][i],
                        'adwords_cost': HISTORICAL_DATA['google'][i],
                        'roadshows': HISTORICAL_DATA['roadshow'][i],
                        'new_coffees': HISTORICAL_DATA['new_coffees'][i]
                    },
                    percentage_changes={},
                    expected_demand=0.0,
                    demand_actualising=percentageChangeDemand,
                    deviation=0.0

                )

                report_card.save()
            except Exception as e:
                print e


