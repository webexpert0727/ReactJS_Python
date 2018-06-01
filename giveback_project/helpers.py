# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import timedelta
from functools import wraps

from django.contrib.gis.geoip import GeoIP
from django.core.mail import EmailMessage
from django.shortcuts import redirect
from django.utils import timezone

from customers.models import Customer
from loyale.models import Helper


geo_ip = GeoIP()
logger = logging.getLogger(__name__)
CTZ = timezone.get_current_timezone()


def send_emails_rewards(request, day):
    try:
        db_helper = Helper.objects.latest('id')
        print len(Helper.objects.all())
    except Exception as e:
        print e
        db_helper = Helper(emails_rewards_sent=False)
        db_helper.save()

    print 'Sent?', db_helper

    if day == 4:
        print 'Today is Thursday!'

        if not db_helper.emails_rewards_sent:

            db_helper.emails_rewards_sent_count = 0
            db_helper.save()

            for cus in Customer.objects.all():
                print 'Send rewards to ', cus

                try:
                    msg = EmailMessage(
                        subject='When you get Hooked, it only gets better.',
                        to=[cus.user.email],
                        from_email='Your Hook Rewards <hola@hookcoffee.com.sg>'
                    )
                    msg.template_name = 'Hook Rewards Programme 2nd update!'
                    msg.merge_vars = {
                        cus.user.email: {
                            'USERNAME': cus.first_name,
                            'POINTS': cus.amount,
                        },
                    }
                    msg.send()

                    logger.debug('REWARDS: Mailchimp template: {}, email_to: {}'.format(msg.template_name, cus.user.email))

                    db_helper.emails_rewards_sent_count += 1
                    db_helper.save()
                except:
                    pass

            # set SENT to True
            db_helper.emails_rewards_sent = True
            db_helper.save()
            print 'Set Sent to True', db_helper

    else:
        # set SENT to False
        db_helper.emails_rewards_sent = False
        db_helper.emails_rewards_sent_count = 0
        db_helper.save()
        print 'Set Sent to False', db_helper


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    elif request.META.get('HTTP_X_REAL_IP'):
        ip = request.META.get('HTTP_X_REAL_IP')
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_session_data(request):
    """Remove sensitive data."""
    return [(key, val) for key, val in request.session.items()
            if 'password' not in key.lower()]


# def geo_check(view_func):
#     '''
#         add is_worldwide variable to the view
#     '''
#     def _decorator(request, *args, **kwargs):
#         if request.user.is_authenticated:
#             try:
#                 customer = Customer.objects.get(user=request.user)
#             except Customer.DoesNotExist:
#                 country_code = None
#             country_code = customer.country
#         else:
#             ip = get_client_ip(request)
#             country_code = geo_ip.country_code(ip)

#         if country_code == 'SG':
#             print 'LOCATION: SINGAPORE'
#             is_worldwide = False
#         else:
#             print 'LOCATION: WORLDWIDE'
#             is_worldwide = True #origin
#             # is_worldwide = False
#         response = view_func(request, is_worldwide, *args, **kwargs)
#         return response
#     return wraps(view_func)(_decorator)


def geo_check(view_func):
    '''
        add is_worldwide variable to the view
    '''
    def _decorator(request, *args, **kwargs):
        request.session['is_worldwide'] = False #temporary, while country choice page is hidden
        if request.user.is_authenticated:
            try:
                customer = Customer.objects.get(user=request.user)
                country_code = customer.country
            except Customer.DoesNotExist:
                country_code = None

            if country_code == 'SG':
                print 'LOCATION: SINGAPORE (authenticated)'
                is_worldwide = False
            else:
                print 'LOCATION: WORLDWIDE (authenticated)'
                is_worldwide = True
                request.session['is_worldwide'] = True #temporary, while country choice page is hidden
        else:
            if 'is_worldwide' in request.session.keys():
                is_worldwide = request.session.get('is_worldwide')
                print 'LOCATION: WORLDWIDE (not authenticated)' if is_worldwide else 'LOCATION: SINGAPORE (not authenticated)'
            else:
                print 'REDIRECT TO INDEX'
                is_worldwide = None
                redirect('index')

        response = view_func(request, is_worldwide, *args, **kwargs)
        return response
    return wraps(view_func)(_decorator)


# def singapore(view_func):
#     '''
#         allow to execute the view within the Singapore only
#     '''
#     def _decorator(request, *args, **kwargs):
#         if request.user.is_authenticated:
#             try:
#                 customer = Customer.objects.get(user=request.user)
#             except Customer.DoesNotExist:
#                 country_code = None
#             country_code = customer.country
#         else:
#             ip = get_client_ip(request)
#             country_code = geo_ip.country_code(ip)
#         if country_code == 'SG':
#             response = view_func(request, *args, **kwargs)
#         else:
#             return redirect('index') #origin
#             # response = view_func(request, *args, **kwargs)
#         return response
#     return wraps(view_func)(_decorator)


def singapore(view_func):
    '''
        allow to execute the view within the Singapore only
    '''
    def _decorator(request, *args, **kwargs):
        request.session['is_worldwide'] = False #temporary, while country choice page is hidden
        if request.user.is_authenticated:
            print '@SINGAPORE authenticated'
            try:
                customer = Customer.objects.get(user=request.user)
                country_code = customer.country
            except Customer.DoesNotExist:
                country_code = None
            if country_code == 'SG':
                response = view_func(request, *args, **kwargs)
            else:
                request.session['is_worldwide'] = True #temporary, while country choice page is hidden
                return redirect('index')
        else:
            print '@SINGAPORE not authenticated!'
            if 'is_worldwide' in request.session.keys():
                print '@SINGAPORE\tnot authenticated!\tis_worldwide in session'
                is_worldwide = request.session.get('is_worldwide', False)
                if not is_worldwide:
                    response = view_func(request, *args, **kwargs)
                else:
                    return redirect('index')
            else:
                print '@SINGAPORE\tnot authenticated!\tis_worldwide not in session!'
                return redirect('index')

        return response
    return wraps(view_func)(_decorator)


def get_shipping_date():
    """Return nearest shipping date."""
    now = CTZ.normalize(timezone.now())
    day = now.isoweekday()
    today = now.replace(hour=12, minute=0, second=0, microsecond=0)
    # noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
    # morning = True if now < noon else False

    # Mon, Tue, Wed, Thu
    if day in range(1, 5):
        # return today if morning else tomorrow
        return today + timedelta(days=1)
    # Friday
    elif day == 5:
        # return today if morning else three_days_later
        return today + timedelta(days=3)
    # Saturday
    elif day == 6:
        return today + timedelta(days=2)
    # Sunday
    elif day == 7:
        return today + timedelta(days=1)

def get_estimated_date(shipping_date=None, x=3, y=2):
    shipping_date = shipping_date or get_shipping_date()
    if shipping_date.weekday() == 0:
        y = 4
    elif shipping_date.weekday() == 1:
        y = 3
    elif shipping_date.weekday() == 2:
        x = 5
    elif shipping_date.weekday() == 3:
        x = 5
    elif shipping_date.weekday() == 4:
        x = 5
    elif shipping_date.weekday() == 5:
        x = 4
    min_shipping_date = shipping_date + timedelta(days=x)
    min_day = min_shipping_date.day
    min_month = min_shipping_date.strftime("%B")
    min_year = min_shipping_date.year
    max_shipping_date = min_shipping_date + timedelta(days=y)
    max_day = max_shipping_date.day
    max_month = max_shipping_date.strftime("%B")
    max_year = max_shipping_date.year
    if min_month == max_month:
        min_month = ""
    else:
        min_month = ' %s' % min_month
    if min_year == max_year:
        min_year = ""
    else:
        min_year = ' %s' % min_year
    return "{}{}{} - {} {} {}".format(
        ordinal(min_day),
        min_month,
        min_year,
        ordinal(max_day),
        max_month,
        max_year
        )

def ordinal(n):
    if 10 <= n % 100 < 20:
        return str(n) + 'TH'
    else:
        return  str(n) + {1 : 'ST', 2 : 'ND', 3 : 'RD'}.get(n % 10, "TH")

def get_interval(plan):
    if plan == 'fortnight':
        return 14
    return 7
