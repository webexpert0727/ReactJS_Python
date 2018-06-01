from decimal import Decimal
import time
from datetime import timedelta, datetime
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
import ast
from coffees.models import RawBean
from customers.models import Customer, Order
from manager import mailing_list
from manager.models import RawBeanStats, Threshold


def getAllBeans():
    beans = RawBean.objects.all()

    result = []

    for bean in beans:
        bean_details = {}
        bean_details['id'] = bean.id
        bean_details['name'] = bean.name
        bean_details['stock'] = float(bean.stock)
        bean_details['status'] = bean.status
        bean_details['created_date'] = bean.created_date
        result.append(bean_details)

    return result


def processAddNewBean(name, stock):

    try:
        stock = float(stock)
    except ValueError:
        return {
            'status' : 500,
            'error_message' : 'Please input a numeric value for STOCK'
        }

    #add bean to database
    try:
        bean = RawBean(
                name=name,
                stock=stock)
        bean.save()
    except IntegrityError:
        return {
            'status' : 500,
            'error_message' : 'Bean already exists in database!'
        }

    #log down stats
    stats = RawBeanStats(
        raw_bean=bean,
        stock=stock
    )
    stats.save()

    return {
        'status' : 200,
        'message' : 'Bean has been successfully added into the inventory!'
    }


def processUpdateBean(update_values):

    for values in update_values:
        bean_id = str(values['bean_id'])
        new_stock = str(values['stock'])
        status = values['status']

        bean_id.strip()
        new_stock.strip()

        #check for empty string
        if bean_id == 'None' or new_stock == 'None' or len(bean_id) == 0 or len(new_stock) == 0:
            return {
                'status': 500,
                'error_message': 'Please input a value!'
            }

        #check for non-numeric input
        try:
            bean_id = int(bean_id)
            new_stock = float(new_stock)
        except ValueError:
            return {
                'status': 500,
                'error_message': 'Please input a numeric value for bean id or stock'
            }

        #check for null status
        if status is None:
            return {
                'status' : 500,
                'error_message' : 'Please input True or False for Bean Status'
            }

        try:
            bean = RawBean.objects.get(id=bean_id)
        except ObjectDoesNotExist:
            return {
                'status' : 500,
                'error_message' : 'Bean does not exist!'
            }

        bean.status = status

        if status == False:

            stats = RawBeanStats(
                raw_bean=bean,
                stock=0,
                status=False
            )
            bean.stock = 0

        else:
            bean.stock = new_stock
            stats = RawBeanStats(
                raw_bean=bean,
                stock=new_stock,
                status=status
            )

        stats.save()
        bean.save()

    return {
        'status' : 200,
        'message' : 'Bean has been successfully updated in the inventory!'
    }


def processGetInactiveBeans():

    inactive_beans = RawBean.objects.filter(status=False)

    if not inactive_beans:
        return {
            'status': 500,
            'error_message': 'There are no inactive beans!'
        }

    else:
        result = []

        try:

            for bean in inactive_beans:

                created_date = bean.created_date

                latest_stat = RawBeanStats.objects.filter(raw_bean=bean, status=False).latest('date')

                last_active_date = latest_stat.date - timedelta(days=1)

                all_stats_for_bean = RawBeanStats.objects.filter(raw_bean=bean)

                stats_except_first = all_stats_for_bean[1:len(all_stats_for_bean)]

                total_roasted = 0

                for stat in stats_except_first:
                    total_roasted += stat.stock

                result.append(
                    {
                        'bean_id' : bean.id,
                        'bean_name': bean.name,
                        'created_date': time.mktime(created_date.timetuple()),
                        'last_active_date': time.mktime(last_active_date.timetuple()),
                        'total_roasted': float(total_roasted)
                    }
                )
        except Exception as e:
            return {
                'status': 500,
                'error_message': str(e)
            }

    return {
        'status' : 200,
        'inactive_beans' : result
    }


def processGetActiveBeans(dates_str):

    dates_str = ast.literal_eval(dates_str)

    dates = []

    try:
        for date_str in dates_str:
            dates.append(datetime.strptime(date_str, '%d-%m-%Y').date())
    except Exception as e:
        return {
            'status' : 500,
            'error_message' : str(e)
        }

    active_beans = RawBean.objects.filter(status=True)

    if active_beans:
        beans = []

        for bean in active_beans:
            bean_details = {}
            bean_details['bean_id'] = bean.id
            bean_details['bean_name'] = bean.name

            weeks = []
            for date in dates:

                try:
                    query_date = date + timedelta(days=1)
                    bean_stats = RawBeanStats.objects.filter(raw_bean=bean, date__lt=query_date).latest('date')

                    weeks.append(
                        {
                            'date': date.strftime('%d-%m-%Y'),
                            'stock': float(bean_stats.stock),
                            'status': bean_stats.status
                        }
                    )

                except ObjectDoesNotExist:
                    weeks.append(
                        {
                            'date': date.strftime('%d-%m-%Y'),
                            'stock': 0,
                            'status': False
                        }
                    )

            bean_details['weeks'] = weeks

            bean_details['estimated_amount_to_roast'] = int(getEstimatedRoastAmount(dates[-1]) / len(active_beans))
            bean_details['estimated_date_to_roast'] = (dates[-1] + timedelta(days=7)).strftime('%d-%m-%Y')

            beans.append(bean_details)

    else:
        return {
            'status': 500,
            'error_message': 'There are no active beans!'
        }

    return {
        'status' : 200,
        'beans' : beans
    }


def getEstimatedRoastAmount(date):
    # y = 14.72911 + 1.254810 * curr_num_active_customers + 0.172784 * num_orders
    numCurrOrders = Order.objects.filter(shipping_date__gt=(date - timedelta(days=7)), shipping_date__lte=date).count()
    num_active_customers = Customer.objects.active().count()


    return (14.72911 + 1.254810 * num_active_customers + 0.172784 * numCurrOrders)* 200/1000


def processUpdateThreshold(threshold):

    try:
        if not threshold:
            if threshold == 0:
                return {
                    'status': 500,
                    'error_message': 'Threshold cannot be equal to zero'
                }
            threshold = Threshold()
        else:
            if threshold < 0:
                return {
                    'status': 500,
                    'error_message': 'Threshold cannot be less than zero'
                }
            threshold = Threshold(amount=threshold)

        threshold.save()

    except Exception as e:
        return {
            'status' : 500,
            'error_message' : str(e)
        }

    return {
        'status' : 200,
        'message' : 'Threshold has been updated!'
    }


def processGetThreshold():

    try:
        threshold = Threshold.objects.latest('date')

    except ObjectDoesNotExist as e:
        return {
        'status' : 200,
        'threshold' : 20.0,
        }

    except Exception as e:
        return {
            'status': 500,
            'error_message': str(e)
        }

    return {
        'status' : 200,
        'threshold' : float(threshold.amount),
    }
