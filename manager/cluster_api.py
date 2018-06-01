from django.utils import timezone

import pandas as pd
import numpy as np
from django.core.exceptions import ObjectDoesNotExist
from pandas import Series

from coffees.models import BrewMethod
from customers.models import Customer, Order
from sklearn.cluster import KMeans
import mailchimp_api as mailchimp
from manager.models import ClusterDF, CustomerCluster


#Mailchimp List IDs for Cluster 0, 1 and 2
CLUSTER_0 = '558263ad91'
CLUSTER_1 = '1590f21986'
CLUSTER_2 = '5fc98780a6'

#Mailchimp List ID for Unsubscribers
UNSUBSCRIBER_LIST_ID = 'f3c530cad0'

CLUSTER_NAMES = {
    'committed' : 'Committed Customers',
    'surfers' : 'Surfers',
    'seekers' : 'Benefit Seekers'
}

CLUSTER_DESCRIPTION = {
    'committed' : 'Customers who are extremely committed to Hook Coffee',
    'surfers' : 'Customers with fast turnover and are continually seeking for new experiences',
    'seekers' : 'Customers who only order when there are extra benefits for them'
}


def getNumberOfOrders(customer_id):
    orders = Order.objects.filter(customer_id=customer_id)
    return len(orders)


def getRatioAmountSpentAgainstTime(customer_id):
    orders = Order.objects.filter(customer_id=customer_id)
    if len(orders) == 0:
        return 0.0
    total_spent = 0
    for order in orders:
        total_spent += order.amount

    earliest_order = orders.earliest('date').date
    today_date = timezone.now()

    delta = today_date - earliest_order

    if delta.days == 0:
        return 0.0

    return float(total_spent) / delta.days


def getNumberOfVouchersUsed(customer_id):
    orders = Order.objects.filter(customer_id=customer_id)
    if len(orders) == 0:
        return 0
    num_vouchers = 0
    for order in orders:
        if order.voucher_id is not None:
            num_vouchers += 1

    return num_vouchers


def getAverageIntervalBetweenOrders(customer_id):
    orders = Order.objects.filter(customer_id=customer_id)
    if len(orders) == 0:
        return 0.0
    total_interval = 0
    for order in orders:
        total_interval += order.interval

    return float(total_interval) / len(orders)


def getTotalAmountSpent(customer_id):
    orders = Order.objects.filter(customer_id=customer_id)
    if len(orders) == 0:
        return 0.0
    total_spent = 0
    for order in orders:
        total_spent += order.amount
    return total_spent


def getNumberOfOneOffOrders(customer_id):
    orders = Order.objects.filter(customer_id=customer_id,
                                  recurrent=False)

    return len(orders)


def getPercentageBrewMethods(customers):
    brewmethods = BrewMethod.objects.all()

    cluster_brew_methods = {}

    for brewmethod in brewmethods:
        cluster_brew_methods[brewmethod.name] = 0

    total_orders = 0

    for customer_id in customers:
        orders = Order.objects.filter(customer_id=customer_id)
        if len(orders) == 0:
            continue
        for order in orders:
            cluster_brew_methods[order.brew.name] += 1
            total_orders += 1

    keys = cluster_brew_methods.keys()
    for key in keys:
        brew_method_number = cluster_brew_methods[key]
        cluster_brew_methods[key] = round((brew_method_number/float(total_orders) * 100.0) , 2)

    return cluster_brew_methods


def batchDeleteMembers(list_id, member_ids):
    json_body = {}
    operations = mailchimp.formOperationsListDeleteMembers(list_id, member_ids)

    json_body['operations'] = operations

    mailchimp.batch(json_body)


def getEmailsFromCustomers(customers, unsubscribers):
    users = [customer.user for customer in customers]
    emails = [user.email for user in users if user.email not in unsubscribers]

    return [email.encode('ascii') for email in emails]


def batchAddMembers(list_id, emails):
    json_body = {}
    operations = mailchimp.formOperationsListsMembers(list_id, emails)

    json_body['operations'] = operations

    mailchimp.batch(json_body)


def createOrUpdateCustomerCluster(cluster_number, cluster_name, cluster_description, mean_orders, mean_ratio_amount_time, mean_vouchers_used, mean_interval, mean_total_spending,
                                  mean_one_off_orders, customers, percentage_brew_methods, cluster_revenue):
    try:
        cluster = CustomerCluster.objects.get(cluster_number=cluster_number)
        cluster.cluster_name = cluster_name
        cluster.cluster_description = cluster_description
        cluster.mean_orders = mean_orders
        cluster.mean_ratio_amount_time = mean_ratio_amount_time
        cluster.mean_vouchers_used = mean_vouchers_used
        cluster.mean_interval = mean_interval
        cluster.mean_total_spending = mean_total_spending
        cluster.mean_one_off_orders = mean_one_off_orders
        cluster.customers = customers
        cluster.percentage_brew_methods = percentage_brew_methods
        cluster.cluster_revenue = cluster_revenue

    except ObjectDoesNotExist:
        cluster = CustomerCluster(
            cluster_number=cluster_number,
            cluster_name=cluster_name,
            cluster_description=cluster_description,
            mean_orders=mean_orders,
            mean_ratio_amount_time=mean_ratio_amount_time,
            mean_vouchers_used=mean_vouchers_used,
            mean_interval=mean_interval,
            mean_total_spending=mean_total_spending,
            mean_one_off_orders=mean_one_off_orders,
            customers=customers,
            percentage_brew_methods=percentage_brew_methods,
            cluster_revenue=cluster_revenue
        )

    cluster.save()


def getTotalRevenueFromCluster(customers):
    total_revenue = 0
    orders = Order.objects.filter(customer__in=customers)
    for order in orders:
        total_revenue += order.amount
    return total_revenue


def processExecuteKMeansClusteringForCustomerSegments():

    customers = Customer.objects.all().values('id')  # select all customer objects, only ID needed for now.

    # convert Django Queryset to Dataframe
    df = pd.DataFrame(list(customers))
    sLength = len(df['id'])

    # create new column for number of orders per customer and average amount spent per customer
    df['num_orders'] = Series(np.random.randn(sLength), index=df.index)
    df['ratio_amount_spent_against_time'] = Series(np.random.randn(sLength), index=df.index)
    df['num_vouchers'] = Series(np.random.randn(sLength), index=df.index)
    df['average_interval'] = Series(np.random.randn(sLength), index=df.index)
    df['total_spending'] = Series(np.random.randn(sLength), index=df.index)
    df['num_one_off_orders'] = Series(np.random.randn(sLength), index=df.index)

    for index, row in df.iterrows():
        df.set_value(index, 'num_orders', getNumberOfOrders(df.loc[index]['id']))
        df.set_value(index, 'ratio_amount_spent_against_time', round(getRatioAmountSpentAgainstTime(df.loc[index]['id'])), 2)
        df.set_value(index, 'num_vouchers', getNumberOfVouchersUsed(df.loc[index]['id']))
        df.set_value(index, 'average_interval', round(getAverageIntervalBetweenOrders(df.loc[index]['id'])), 2)
        df.set_value(index, 'total_spending', round(getTotalAmountSpent(df.loc[index]['id'])), 2)
        df.set_value(index, 'num_one_off_orders', round(getNumberOfOneOffOrders(df.loc[index]['id'])), 2)

    # df = df.as_matrix(columns= ["num_orders","average_amount_spent","num_vouchers", "average_interval"])
    cluster_by = df.as_matrix(columns=["num_orders", "ratio_amount_spent_against_time"])

    k = 3   #fix k = 3
    model = KMeans(n_clusters=k)
    df['cluster'] = model.fit_predict(cluster_by)

    #save dataframe into ClusterDF object
    cluster_df = ClusterDF()
    cluster_df.data = df
    cluster_df.save()

    df['is_0'] = df.cluster == 0
    df['is_1'] = df.cluster == 1
    df['is_2'] = df.cluster == 2

    #calculate mean number of orders
    cluster_0_mean_num_orders = df[df['is_0']].num_orders.mean()
    cluster_1_mean_num_orders = df[df['is_1']].num_orders.mean()
    cluster_2_mean_num_orders = df[df['is_2']].num_orders.mean()

    #calculate mean ratio of amount spent against time
    cluster_0_mean_ratio = df[df['is_0']].ratio_amount_spent_against_time.mean()
    cluster_1_mean_ratio = df[df['is_1']].ratio_amount_spent_against_time.mean()
    cluster_2_mean_ratio = df[df['is_2']].ratio_amount_spent_against_time.mean()

    #calculate mean number of vouchers used
    cluster_0_mean_num_vouchers = df[df['is_0']].num_vouchers.mean()
    cluster_1_mean_num_vouchers = df[df['is_1']].num_vouchers.mean()
    cluster_2_mean_num_vouchers = df[df['is_2']].num_vouchers.mean()

    # calculate mean interval between orders
    cluster_0_mean_interval = df[df['is_0']].average_interval.mean()
    cluster_1_mean_interval = df[df['is_1']].average_interval.mean()
    cluster_2_mean_interval = df[df['is_2']].average_interval.mean()

    #calculate mean total amount spent
    cluster_0_mean_total_spending = df[df['is_0']].total_spending.mean()
    cluster_1_mean_total_spending = df[df['is_1']].total_spending.mean()
    cluster_2_mean_total_spending = df[df['is_2']].total_spending.mean()

    # calculate mean number of one off orders
    cluster_0_mean_one_off_orders = df[df['is_0']].num_one_off_orders.mean()
    cluster_1_mean_one_off_orders = df[df['is_1']].num_one_off_orders.mean()
    cluster_2_mean_one_off_orders = df[df['is_2']].num_one_off_orders.mean()

    #retrieve customers in specific clusters
    cluster_groupby_0 = df.loc[df['cluster'] == 0]
    cluster_0_customers = cluster_groupby_0['id']
    cluster_0_customers = list(cluster_0_customers.values.flatten())
    cluster_0_dict = {
        'customers' : map(lambda x: int(x), cluster_0_customers)
    }

    cluster_groupby_1 = df.loc[df['cluster'] == 1]
    cluster_1_customers = cluster_groupby_1['id']
    cluster_1_customers = list(cluster_1_customers.values.flatten())
    cluster_1_dict = {
        'customers' : map(lambda x: int(x), cluster_1_customers)
    }

    cluster_groupby_2 = df.loc[df['cluster'] == 2]
    cluster_2_customers = cluster_groupby_2['id']
    cluster_2_customers = list(cluster_2_customers.values.flatten())
    cluster_2_dict = {
        'customers' : map(lambda x: int(x), cluster_2_customers)
    }

    #calculate percentage by brew methods for each cluster
    cluster_0_percentage_brew_methods = getPercentageBrewMethods(cluster_0_customers)
    cluster_1_percentage_brew_methods = getPercentageBrewMethods(cluster_1_customers)
    cluster_2_percentage_brew_methods = getPercentageBrewMethods(cluster_2_customers)

    # retrieve customer objects using customer IDs
    customers_0 = Customer.objects.filter(id__in=cluster_0_customers)
    customers_1 = Customer.objects.filter(id__in=cluster_1_customers)
    customers_2 = Customer.objects.filter(id__in=cluster_2_customers)

    #get total revenue from cluster
    cluster_0_revenue = getTotalRevenueFromCluster(customers_0)
    cluster_1_revenue = getTotalRevenueFromCluster(customers_1)
    cluster_2_revenue = getTotalRevenueFromCluster(customers_2)

    #to find out which cluster has the highest/lowest/middle number of mean number of orders
    #assign cluster name and description accordingly
    mean_orders_dict = {
        'cluster_0' : cluster_0_mean_num_orders,
        'cluster_1' : cluster_1_mean_num_orders,
        'cluster_2' : cluster_2_mean_num_orders
    }

    key_with_max_orders = max(mean_orders_dict.iterkeys(), key=(lambda key: mean_orders_dict[key]))
    key_with_min_orders = min(mean_orders_dict.iterkeys(), key=(lambda key: mean_orders_dict[key]))

    if key_with_max_orders == 'cluster_0':
        cluster_0_name = CLUSTER_NAMES['committed']
        cluster_0_description = CLUSTER_DESCRIPTION['committed']
    elif key_with_max_orders == 'cluster_1':
        cluster_1_name = CLUSTER_NAMES['committed']
        cluster_1_description = CLUSTER_DESCRIPTION['committed']
    else:
        cluster_2_name = CLUSTER_NAMES['committed']
        cluster_2_description = CLUSTER_DESCRIPTION['committed']

    if key_with_min_orders == 'cluster_0':
        cluster_0_name = CLUSTER_NAMES['seekers']
        cluster_0_description = CLUSTER_DESCRIPTION['seekers']
    elif key_with_min_orders == 'cluster_1':
        cluster_1_name = CLUSTER_NAMES['seekers']
        cluster_1_description = CLUSTER_DESCRIPTION['seekers']
    else:
        cluster_2_name = CLUSTER_NAMES['seekers']
        cluster_2_description = CLUSTER_DESCRIPTION['seekers']

    #remove key/value pairs that have already been used
    mean_orders_dict.pop(key_with_max_orders)
    mean_orders_dict.pop(key_with_min_orders)

    #get remaining key which represents the middle cluster
    remaining_key = mean_orders_dict.keys()[0]

    if remaining_key == 'cluster_0':
        cluster_0_name = CLUSTER_NAMES['surfers']
        cluster_0_description = CLUSTER_DESCRIPTION['surfers']
    elif remaining_key == 'cluster_1':
        cluster_1_name = CLUSTER_NAMES['surfers']
        cluster_1_description = CLUSTER_DESCRIPTION['surfers']
    else:
        cluster_2_name = CLUSTER_NAMES['surfers']
        cluster_2_description = CLUSTER_DESCRIPTION['surfers']


    createOrUpdateCustomerCluster(0, cluster_0_name, cluster_0_description, cluster_0_mean_num_orders, cluster_0_mean_ratio, cluster_0_mean_num_vouchers, cluster_0_mean_interval,
                                  cluster_0_mean_total_spending, cluster_0_mean_one_off_orders, cluster_0_dict, cluster_0_percentage_brew_methods, cluster_0_revenue)

    createOrUpdateCustomerCluster(1, cluster_1_name, cluster_1_description, cluster_1_mean_num_orders, cluster_1_mean_ratio, cluster_1_mean_num_vouchers, cluster_1_mean_interval,
                                  cluster_1_mean_total_spending, cluster_1_mean_one_off_orders, cluster_1_dict, cluster_1_percentage_brew_methods, cluster_1_revenue)

    createOrUpdateCustomerCluster(2, cluster_2_name, cluster_2_description, cluster_2_mean_num_orders, cluster_2_mean_ratio, cluster_2_mean_num_vouchers, cluster_2_mean_interval,
                                  cluster_2_mean_total_spending, cluster_2_mean_one_off_orders, cluster_2_dict, cluster_2_percentage_brew_methods, cluster_2_revenue)


    #for each of the 3 mailing lists corresponding to the 3 clusters, retrieve them using the mailchimp api
    #check for existing members, store their MD5 Hash ID into an array
    #delete all the members using their MD5 hash id
    #retrieve latest customer emails using customer IDs
    #add customers to respective mailing list

    #delete all members from respective lists
    #key error due to empty list
    try:
        list_cluster_0_members = mailchimp.getMailchimpListMembers(CLUSTER_0, 99999, 0)['members']
        cluster_0_members_ids = [member['id'] for member in list_cluster_0_members]
        cluster_0_members_ids = [id.encode('ascii') for id in cluster_0_members_ids]
        batchDeleteMembers(CLUSTER_0, cluster_0_members_ids)
    except KeyError:
        pass

    try:
        list_cluster_1_members = mailchimp.getMailchimpListMembers(CLUSTER_1, 99999, 0)['members']
        cluster_1_members_ids = [member['id'] for member in list_cluster_1_members]
        cluster_1_members_ids = [id.encode('ascii') for id in cluster_1_members_ids]
        batchDeleteMembers(CLUSTER_1, cluster_1_members_ids)
    except KeyError:
        pass

    try:
        list_cluster_2_members = mailchimp.getMailchimpListMembers(CLUSTER_2, 99999, 0)['members']
        cluster_2_members_ids = [member['id'] for member in list_cluster_2_members]
        cluster_2_members_ids = [id.encode('ascii') for id in cluster_2_members_ids]
        batchDeleteMembers(CLUSTER_2, cluster_2_members_ids)
    except KeyError:
        pass

    #retrieve list of people of have unsubscribed
    unsubscribers = mailchimp.getMailchimpListMembers(UNSUBSCRIBER_LIST_ID, 99999, 0)['members']
    unsubscribers_emails = [member['email_address'] for member in unsubscribers]

    #retrieve emails in clusters that exclude unsubscribers
    cluster_0_emails = getEmailsFromCustomers(customers_0, unsubscribers_emails)
    cluster_1_emails = getEmailsFromCustomers(customers_1, unsubscribers_emails)
    cluster_2_emails = getEmailsFromCustomers(customers_2, unsubscribers_emails)

    #add members in mailchimp lists
    try:
        batchAddMembers(CLUSTER_0, cluster_0_emails)
        batchAddMembers(CLUSTER_1, cluster_1_emails)
        batchAddMembers(CLUSTER_2, cluster_2_emails)

    except Exception as e:
        return {
            'status': 500,
            'error_message': str(e)
        }

    return {
        'status' : 200,
        'message' : 'KMeans was successful'
    }


