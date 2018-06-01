# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import logging
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_UP

from jsonview.decorators import json_view

import pytz

import requests

import stripe

from unidecode import unidecode

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from coffees.models import (
    BrewMethod, CoffeeGear, CoffeeGearColor, CoffeeType, Flavor,WorkShops)
from coffees.views import get_shipping_rates

from customauth.models import MyUser

from customers.forms import AddressForm, GiftAddressForm, GS_CustomerForm, GS_PreferencesForm
from customers.models import (
    Address, CardFingerprint, Customer, FacebookCustomer, GearOrder,
    Order, Preferences, Reference, Referral, ShoppingCart, Voucher, WorkShopOrder)
from customers.tasks import (
    add_event, add_tag, mailchimp_subscribe, send_email_async)

from get_started.do_registration import do_registration, START_DATE, END_DATE, NEW_DATE
from get_started.forms import GetStartedResponseForm, CustomRegistrationForm
from get_started.helpers import createOrder, generate_securerandompass, vouchers_allowed
from get_started.models import GetStartedResponse

from giveback_project.helpers import (
    geo_check, get_client_ip, get_estimated_date,
    get_session_data, get_shipping_date, singapore)

from manager.mailing_list import is_tracked
from manager.models import MailchimpCampaignStats

from reminders.models import Reminder
from .stripe_api import charge as charge_stripe


stripe.api_key = settings.SECRET_KEY
logger = logging.getLogger('giveback_project.' + __name__)

CTZ = timezone.get_current_timezone()


def flush_session(request):
    '''Retain is_worldwide value in session'''
    tmp_is_worldwide = request.session.get('is_worldwide', None)
    request.session.flush()
    if tmp_is_worldwide is not None:
        request.session.set_expiry(0)
        request.session['is_worldwide'] = tmp_is_worldwide


@singapore
def index(request):
    logger.debug(
        'GetStarted:index:init:%s:%s',
        get_client_ip(request), get_session_data(request))

    f = forms.CharField()

    if request.method == 'GET':
        if is_tracked(request):
            try:
                campaign_id = request.session['campaign_id']
                email = request.session['campaign_email']

                flush_session(request)

                request.session['campaign_id'] = campaign_id
                request.session['campaign_email'] = email
                existing_stats = MailchimpCampaignStats.objects.get(campaign_id=campaign_id, email=email)
                if existing_stats.action != MailchimpCampaignStats.PURCHASED:
                    existing_stats.action = MailchimpCampaignStats.GET_STARTED
                    existing_stats.save()
            except Exception:
                logger.error(
                    'GetStarted:index:init:%s:%s',
                    get_client_ip(request), get_session_data(request), exc_info=True)

        else:
            flush_session(request)

        ref = request.GET.get('ref')
        if ref:
            request.session['ref'] = f.clean(ref)

        email = request.GET.get('email')
        if email:
            try:
                gs_response = GetStartedResponse.objects.filter(
                    email=email).latest('created')
            except GetStartedResponse.DoesNotExist:
                logger.error(
                    'Cannot find GetStartedResponse: %s', email, exc_info=True)
            else:
                _load_session(request, gs_response)

                request.session['chosen_voucher'] = request.GET.get('voucher', '')
                if request.GET.get("coffee"):
                    request.session["coffee"] = request.GET.get("coffee")

                is_nespresso = request.session['brew_title'] == _('Nespresso')
                if is_nespresso:
                    return redirect('register_nespresso')
                else:
                    return redirect('register')

    context = {}

    flavors = Flavor.objects.all()
    bags_list = CoffeeType.objects.bags().filter(special=False)
    pods_list = CoffeeType.objects.nespresso().filter(special=False)

    context['brew_methods'] = BrewMethod.objects.sorted()
    context['flavors'] = flavors
    context['bags_list'] = bags_list
    context['pods_list'] = pods_list

    form = GetStartedResponseForm()

    chosen_voucher = request.POST.get('chosen_voucher')

    if request.method == 'POST' and chosen_voucher:
        request.session['chosen_voucher'] = f.clean(chosen_voucher)
    elif request.method == 'POST':
        request.session['user_info'] = request.POST.get('user_info')
        form = _get_intro_form(request, context)
    context['form'] = form

    logger.debug(
        'GetStarted:index:render:%s:%s',
        get_client_ip(request), get_session_data(request))
    return render(request, 'get_started/get_started.html', context)


@json_view
def recommend(request):
    if request.method == 'POST':

        details = json.loads(request.session['user_info'])

        name = request.session['name']
        email = request.session['email']
        method = details["method"]
        flavours = details["flavour"]
        intensity = details["intensity"]
        ref = request.session.get('ref')
        accesstoken = request.session.get('accesstoken')
        if ref:
            details['ref'] = ref
        if accesstoken:
            details['accesstoken'] = accesstoken

        try:
            brew_method = BrewMethod.objects.get(id=method)
            brew_title = brew_method.name
        except Exception:
            logger.error(
                'Cannot get chosen brew method: %s', email, exc_info=True)
            brew_title = _('Espresso')
            brew_method = BrewMethod.objects.get(name=brew_title)

        coffee_list = (
            CoffeeType.objects.non_tasters().filter(special=False)
            .values('id', 'body', 'brew_method', 'profile'))

        print 'Coffee list:'
        for show_coffee in coffee_list:
            print show_coffee['id'], ': ', CoffeeType.objects.get(id=show_coffee['id'])
            print '\t:::', show_coffee

        turn_1 = []
        for coffee in coffee_list:
            if coffee['body'] == intensity:
                turn_1.append(coffee)

        if not turn_1:
            intensity_up = intensity + 1
            intensity_down = intensity - 1
            for coffee in coffee_list:
                if coffee['body'] in [intensity_up, intensity_down]:
                    turn_1.append(coffee)

        print 'By intensity:'
        for t1 in turn_1:
            print t1['id']

        if turn_1:
            # Turn 2: Brew method
            turn_2 = []
            for coffee in turn_1:
                if coffee['brew_method'] == method:
                    turn_2.append(coffee)

            print 'By brew method:'
            for t2 in turn_2:
                print t2['id']

            if not turn_2:
                turn_2 = (
                    CoffeeType.objects.non_tasters()
                    .filter(brew_method=brew_method, special=False)
                    .values('id', 'body', 'brew_method', 'profile'))

                print 'By brew method (exception):'
                for t2 in turn_2:
                    print t2['id']

            # Turn 3: Flavours
            turn_3 = {}
            for coffee in turn_2:
                turn_3[coffee['id']] = 0.
                for k, v in coffee['profile'].items():
                    if float(k) in flavours:
                        turn_3[coffee['id']] += float(v)

            print 'By flavours:'
            for t3 in turn_3:
                print t3, turn_3[t3]

            try:
                choice = max(turn_3, key=turn_3.get)
                print 'Recommend:', choice
            except ValueError:
                # turn_3 is empty
                choice = random.choice(turn_1)['id']
        else:
            print 'No match by intensity!'
            choice = None

        if not choice:
            # Choose randomly
            choice = (
                CoffeeType.objects.non_tasters()
                .filter(brew_method=brew_method, special=False)
                .first().id)

        try:
            gs_response = GetStartedResponse.objects.filter(
                    email=email).latest('created')
            gs_response.form_details = details
        except:
            gs_response = GetStartedResponse(name=name, email=email)
            gs_response.form_details = details

        gs_response.ct_id = choice
        gs_response.save()

        mailchimp_subscribe.delay(
            email=email,
            merge_vars={'FNAME': request.session.get('name')},
        )

        try:
            coffee = CoffeeType.objects.get(id=choice)
        except:
            coffee = None

        if coffee:
            if coffee.img:
                coffee_image = coffee.img.url
            else:
                coffee_image = None

        request.session['coffee'] = coffee.id
        request.session['default_pack'] = details['default_pack']
        request.session['brew_title'] = brew_method.name
        request.session['from_get_started'] = True
        request.session['from_shopping_cart'] = False

        with_credits = False
        if request.session.get('credits'):
            with_credits = True

        return {
            'name': name,
            'email': email,
            'coffee': coffee.name,
            'img': coffee_image,
            'description': coffee.more_taste,
            'brew_method': brew_method.id,
            'brew_title': brew_method.name,
            'with_credits': with_credits,
        }


@json_view
def register(request):
    """
    Process user registration

    Collect user's information and add him to database.
    """
    return do_registration(request, is_nespresso=False)


@json_view
def register_nespresso(request):
    context = {}

    return do_registration(request, is_nespresso=True)


@json_view
def another(request):
    if request.method == 'POST':

        details = json.loads(request.session['user_info'])
        name = details.get('name') or request.session.get('name')
        email = details.get('email') or request.session.get('email')

        try:
            coffee = CoffeeType.objects.get(id=request.POST['coffee_id'])
        except Exception:
            logger.error(
                'Cannot get another coffee: %s',
                request.session.get('email'),
                extra={'data': {'coffee': request.POST.get('coffee_id')}},
                exc_info=True)

        if coffee.img:
            coffee_image = coffee.img.url
        else:
            coffee_image = None

        try:
            # TODO
            gs_response = GetStartedResponse.objects.filter(
                email=email).latest('created')
            gs_response.ct = coffee
            gs_response.save()
        except Exception:
            logger.error(
                'Error when trying choose another coffee: %s',
                request.session.get('email'),
                extra={'data': {'coffee': request.POST.get('coffee_id')}},
                exc_info=True)

        request.session['coffee'] = coffee.id

        return {
            'another': True,
            'name': name,
            'email': email,
            'coffee': coffee.name,
            'img': coffee_image,
            'description': coffee.more_taste,
        }


def preregister(request, coffee_id, isNespresso, isOneoff, isBottled=False):
    # flush_session(request)
    request.session["referral_voucher"] = None
    request.session["voucher"] = None

    isNespresso = isNespresso == 'True'
    isOneoff = isOneoff == 'True'
    request.session['alacarte'] = isOneoff
    request.session['coffee'] = coffee_id
    request.session['from_get_started'] = False
    request.session['from_shopping_cart'] = False
    request.session['from_preregister'] = True
    request.session['isBottled'] = isBottled

    if isOneoff:
        request.session['active_tab'] = 'active_one_offs'
    elif not isOneoff and isNespresso:
        request.session['active_tab'] = 'active_subscriptions_pods'
    elif isBottled:
        request.session['active_tab'] = 'active_subscriptions_bottled'
    elif not isOneoff and not isNespresso:
        request.session['active_tab'] = 'active_subscriptions'

    try:
        coffee = CoffeeType.objects.get(id=coffee_id)
    except Exception:
        coffee = None

    if coffee:
        if coffee.name == 'Lunar Gift Set':
            request.session['gift'] = True
            request.session['default_pack'] = Preferences.GRINDED

        if isNespresso:
            return redirect('register_nespresso')
        else:
            return redirect('register')

    return redirect('coffees')


def preregister_gear(request, gear_id, gear_qty=1, gear_color_id=0):
    print "preregister_gear() id:", gear_id
    gear_packaging = request.session.get('gear_packaging')
    gear_brew_method = request.session.get('gear_brew_method')
    gear_voucher = request.session.get('gear_voucher')

    flush_session(request)

    f = forms.IntegerField()
    request.session['gear_id'] = f.clean(gear_id)
    request.session['gear_qty'] = abs(f.clean(gear_qty))
    request.session['gear_color_id'] = f.clean(gear_color_id)
    request.session['active_tab'] = 'active_one_offs'
    request.session['gear_packaging'] = gear_packaging
    request.session['gear_brew_method'] = gear_brew_method
    request.session['gear_voucher'] = gear_voucher

    gear = CoffeeGear.objects.filter(id=gear_id).exists()

    if gear:
        return redirect('register_gear')
    else:
        return redirect('shop-gift')


@json_view
def register_credits(request):
    """User registration with initial credits

    Users came from 'Send a friend' offer
    """

    result = context = {}

    if request.method == "POST":

        if 'one-password1' in request.POST:
            rf = CustomRegistrationForm(request.POST, prefix='one')
            if rf.is_valid():
                result['success'] = True
                details = json.loads(request.POST.get('array'))
                request.session['email'] = rf.cleaned_data['email']
                if 'accesstoken' in request.session:
                    request.session['password'] = generate_securerandompass(64)
                else:
                    request.session['password'] = request.POST['one-password1']
                request.session['brew'] = details['brew']
                request.session['package'] = details['package']
                request.session['interval'] = details['interval']
                request.session['different'] = details['different']
            else:
                return HttpResponse(json.dumps(rf.errors))

        if 'two-first_name' in request.POST:
            context = {}
            cf = GS_CustomerForm(request.POST, prefix='two')
            pf = GS_PreferencesForm(request.POST, prefix='tri')
            email = request.session.get('email')

            if cf.is_valid():
                result['success'] = True
                request.session['first_name'] = request.POST['two-first_name']
                request.session['last_name'] = request.POST['two-last_name']
                request.session['country'] = request.POST.get('two-country', 'SG')
                request.session['line1'] = request.POST['two-line1']
                request.session['line2'] = request.POST['two-line2']
                request.session['postcode'] = request.POST['two-postcode']
                request.session['phone'] = request.POST['two-phone']

            else:
                return HttpResponse(json.dumps(cf.errors))

            try:
                user = MyUser(email=email)
                user.set_password(request.session['password'])
                user.save()
                logger.debug('User created: %s', user)
            except Exception:
                logger.error('User not created: %s', email, exc_info=True)

            try:
                customer = Customer.objects.create(
                    user=user,
                    first_name=request.session['first_name'],
                    last_name=request.session['last_name'],
                    amount=request.session.get('credits', 0),
                    country=request.session['country'],
                    line1=request.session['line1'],
                    line2=request.session['line2'],
                    postcode=request.session['postcode'],
                    phone=request.session['phone'],
                )
                logger.debug('Customer created: %s', customer)
                # Add newly created customauth as a Foreign Key reference to FacebookCustomer
                try:
                    facebook_customer = FacebookCustomer.objects.filter(
                        email=email).update(customer=user)
                    if facebook_customer:
                        add_tag.delay(customer_id=customer.id, tag='Facebook')
                except Exception:
                    logger.error('Cannot update FacebookCustomer: %s', email,
                                 exc_info=True)
            except Exception:
                logger.error('Customer not created: %s', email, exc_info=True)

            try:
                if request.session.get('from_preregister'):
                    response = None
                    preferences = Preferences(customer=customer)
                    preferences.coffee = coffee = CoffeeType.objects.get(id=request.session.get('coffee'))
                else:
                    response = GetStartedResponse.objects.filter(
                        email=user.email).latest('created')

                    flavor_ids = []
                    for ch in response.form_details['flavour']:
                        if ch.isdigit():
                            flavor_ids.append(int(ch))

                    flavors = []
                    for flav in flavor_ids:
                        flavors.append(Flavor.objects.get(id=flav))

                    preferences = Preferences(customer=customer)
                    preferences.coffee = coffee = CoffeeType.objects.get(id=request.session.get('coffee'))
                    preferences.save()

                    preferences.intense = response.form_details['intensity']

                    preferences.flavor = flavors
            except Exception:
                preferences = Preferences(customer=customer)
                preferences.coffee = coffee = CoffeeType.objects.get(id=request.session.get('coffee'))

            if request.session.get('alacarte'):
                price = coffee.amount_one_off
            else:
                price = coffee.amount

            try:
                if response:
                    brew = BrewMethod.objects.get(id=response.form_details['method'])
                else:
                    brew_title = request.session.get('brew_title') or _('None')
                    brew = BrewMethod.objects.get(name=brew_title)
                preferences.brew = brew
            except Exception:
                brew_title = request.session.get('brew_title') or _('Espresso')
                brew = BrewMethod.objects.get(name=brew_title)
                preferences.brew = brew

            preferences.package = request.session['package']
            preferences.interval = int(request.session['interval'])
            preferences.different = True if request.session['different'] else False
            preferences.save()

            try:
                voucher = Voucher.objects.get(name=request.session['voucher'])
                if voucher:
                    price -= price * voucher.discount / 100 + voucher.discount2

                    # Mark voucher as used for current customer
                    customer.vouchers.add(voucher)
                    customer.save()
                    voucher.count += 1
                    voucher.save()

            except Exception:
                voucher = None

            if request.session.get('alacarte') or request.session.get('gift'):
                is_recurrent = False
            else:
                is_recurrent = True

            if request.session.get('gift'):
                shipping_date = datetime(2016, 2, 1, 0, 0, 0, 0, pytz.timezone('Asia/Singapore'))
            else:
                shipping_date = get_shipping_date()

            try:
                brew_method = BrewMethod.objects.get(id=request.session['brew'])
                preferences.brew = brew_method
                preferences.save()
            except Exception:
                brew_method = preferences.brew

            # Subscribe customer
            try:
                order = Order(
                    customer=customer,
                    coffee=coffee,
                    date=timezone.now(),
                    shipping_date=shipping_date,
                    amount=price,
                    interval=preferences.interval,
                    recurrent=is_recurrent,
                    status=Order.ACTIVE,
                    brew=brew_method,
                    package=preferences.package,
                    different=preferences.different,
                    voucher=voucher
                )

                order.details['friend'] = request.session.get('friend')
                order.save()

                if voucher:
                    if voucher.name in settings.GIFT_VOUCHERS:
                        order.details[voucher.name] = True
                        order.save()

                add_event.delay(
                    customer_id=customer.id,
                    event='signed-up',
                    data={'credits': round(customer.amount, 2)})
                add_event.delay(
                    customer_id=customer.id,
                    event='created-subscription' if is_recurrent else 'created-one-off',
                    order_id=order.id)

            except Exception:
                order = None

            # Create referral code for new user
            Referral.objects.create(
                user=user,
                code=Referral.get_random_code(customer=customer)
            )

            # Use referral link
            ref = request.session.get('ref', '')
            if ref:
                try:
                    referrer = user
                    referred = Referral.objects.get(code=ref).user
                    Reference.objects.create(referrer=referrer, referred=referred)

                    try:
                        current_user = MyUser.objects.get_by_natural_key(referred.email)
                        current_customer = Customer.objects.get(user=current_user)
                        current_order = Order.objects\
                            .filter(customer=current_customer)\
                            .filter(status__in=['AC', 'PA'])\
                            .latest('date')
                    except:
                        current_order = None

                    if current_order:
                        new_price = current_order.amount - 5
                        if new_price < 0:
                            new_price = 0
                        current_order.amount = new_price
                        current_order.save()

                    # When referred 3 times give him a bonus
                    cnt = Reference.objects.filter(referred=referred).count()
                    if cnt == 3:
                        ref_cus = Customer.objects.get(user=referred)
                        ref_pref = Preferences.objects.get(customer=ref_cus)
                        ref_pref.present_next = True
                        ref_pref.save()

                except Exception:
                    logger.error(
                        'Registration by credits: %s',
                        request.session.get('email'), exc_info=True)

            Reminder.objects.filter(email=user.email).update(completed=True)

            new_user = authenticate(
                email=user.email,
                password=request.session['password'])
            login(request, new_user)

            context = {
                'coffee': coffee.name,
                'image': coffee.img.url,
            }

            roasted_date = ''
            if order.coffee.roasted_on:
                roasted_date = datetime.strftime(order.coffee.roasted_on, '%d/%m/%y')

            # Send summary email
            if order.customer.amount > 18:
                roasted_date = ''
                if order.coffee.roasted_on:
                    roasted_date = datetime.strftime(order.coffee.roasted_on, '%d/%m/%y')

                send_email_async.delay(
                    subject='Your next bag of coffee is leaving the Roastery!',
                    template='Gift Recipient’s Confirmation Email',
                    to_email=order.customer.get_email(),
                    merge_vars={
                        'USERNAME': order.customer.first_name,
                        'CREDITS': str(order.customer.amount - order.coffee.amount),
                        'SENDER': order.details.get('friend') or 'your friend',
                        'COFFEE': order.coffee.name,
                        'ROASTED_ON': roasted_date,
                        'BREW': order.brew.name,
                        'PACKAGE': order.get_package_display(),
                        'PRICE': '%s SGD' % order.amount,
                        'SHIPPING_DATE': datetime.strftime(order.shipping_date, '%d/%m/%y'),
                        'DOMAIN_NAME': request.META.get('HTTP_HOST'),
                    }
                )
            else:
                # one-off
                pass

            return render(request, 'get_started/thankyou.html', context)

        return result

    else:
        username = email = coffee = default_pack = brew_title = ''
        try:
            username = request.session.get('name')
            email = request.session.get('email')
            default_pack = request.session.get('default_pack')\
                or Preferences.WHOLEBEANS
            if request.session.get('V60STARTER'):
                default_pack = Preferences.GRINDED
            brew_title = request.session.get('brew_title') or _('Espresso')

        except Exception:
            logger.error(
                'Error on registration by credits: %s',
                request.session.get('email'),
                exc_info=True)

        brew_methods = BrewMethod.objects.sorted(~Q(name_en='Nespresso'))

        rf = CustomRegistrationForm(prefix='one', initial={
            'username': username,
            'email': email,
        })
        cf = GS_CustomerForm(prefix='two')
        pf = GS_PreferencesForm(prefix='tri')

        try:
            coffee = CoffeeType.objects.get(id=request.session.get('coffee'))
            price = coffee.amount

            if request.session.get('alacarte'):
                price = coffee.amount_one_off

        except Exception:
            coffee = None
            return render(request, 'coffees/index.html')

        try:
            voucher = Voucher.objects.get(name=request.session.get('voucher'))
            if voucher:
                price -= price * voucher.discount / 100 + voucher.discount2
        except:
            pass

    context = {
        'reg_form': rf,
        'cus_form': cf,
        'pre_form': pf,
        'coffee': coffee,
        'price': price,
        'brew_title': brew_title,
        'brew_methods': brew_methods,
        'alacarte': request.session.get('alacarte'),
        'default_pack': default_pack,
        'shipping_date': get_shipping_date(),
        'stripe_key': settings.PUBLISHABLE_KEY,
    }

    return render(request, 'get_started/registration-credits.html', context)


def register_gear(request):
    print "register_gear()"
    result = context = {}

    if request.method == "POST":

        if 'one-password1' in request.POST:
            rf = CustomRegistrationForm(request.POST, prefix='one')
            if rf.is_valid():
                result['success'] = True

                request.session['email'] = rf.cleaned_data['email']
                mailchimp_subscribe.delay(email=request.session.get('email'))

                if 'accesstoken' in request.session:
                    request.session['password'] = generate_securerandompass(64)
                else:
                    request.session['password'] = request.POST['one-password1']
            else:
                errors = rf.errors
                return JsonResponse(errors)

        if 'two-first_name' in request.POST:
            cf = GS_CustomerForm(request.POST, prefix='two')
            pf = GS_PreferencesForm(request.POST, prefix='tri')

            if cf.is_valid():
                result['success'] = True

                request.session['first_name'] = request.POST['two-first_name']
                request.session['last_name'] = request.POST['two-last_name']
                request.session['country'] = request.POST.get('two-country', 'SG')
                request.session['line1'] = request.POST['two-line1']
                request.session['line2'] = request.POST['two-line2']
                request.session['postcode'] = request.POST['two-postcode']
                request.session['phone'] = request.POST['two-phone']

                mailchimp_subscribe.delay(
                    email=request.session.get('email'),
                    merge_vars={
                        'FNAME': request.session.get('first_name'),
                        'LNAME': request.session.get('last_name'),
                    },
                )

            else:
                return JsonResponse(cf.errors)

        if 'voucher' in request.POST:
            email = request.session.get('email')
            now = timezone.now()

            try:
                user = MyUser(email=email)
                user.set_password(request.session.get('password'))
                user.save()
                logger.debug('User created: %s', user)
            except Exception:
                logger.error('User not created: %s', email, exc_info=True)

            try:
                customer = Customer.objects.create(
                    user=user,
                    first_name=request.session.get('first_name'),
                    last_name=request.session.get('last_name'),
                    country=request.session.get('country'),
                    line1=request.session.get('line1'),
                    line2=request.session.get('line2'),
                    postcode=request.session.get('postcode'),
                    phone=request.session.get('phone'),
                    stripe_id=request.session.get('stripe_id'),
                    card_details='{}{}{}'.format(
                        request.session.get('last4'),
                        '{:0>2}'.format(
                            request.session.get('exp_month')),
                        request.session.get('exp_year')
                    ))
                logger.debug('Customer created: %s', customer)

                # add newly created customauth as a Foreign Key reference to FacebookCustomer
                try:
                    facebook_customer = FacebookCustomer.objects.filter(
                        email=email).update(customer=user)
                    if facebook_customer:
                        add_tag.delay(customer_id=customer.id, tag='Facebook')
                except Exception:
                    logger.error('Cannot update FacebookCustomer: %s', email,
                                 exc_info=True)
            except Exception as e:
                logger.error('Customer not created: %s\n%s', email, e, exc_info=True)

            try:
                response = GetStartedResponse.objects.filter(
                    email=user.email).latest('created')

                flavor_ids = []
                for ch in response.form_details['flavour']:
                    if ch.isdigit():
                        flavor_ids.append(int(ch))

                flavors = []
                for flav in flavor_ids:
                    flavors.append(Flavor.objects.get(id=flav))

                preferences = Preferences(customer=customer)
                preferences.coffee = coffee = response.ct
                preferences.save()

                preferences.intense = response.form_details['intensity']
                preferences.flavor = flavors
            except Exception:
                preferences = Preferences(customer=customer)
                preferences.coffee = coffee = None

            preferences.save()

            gear = CoffeeGear.objects.get(id=request.session.get('gear_id'))
            order_details = {}

            gear_color_id = request.session.get('gear_color_id')
            if gear_color_id:
                color = CoffeeGearColor.objects.get(id=gear_color_id)
                order_details['Colour'] = color.name

            gear_qty = request.session.get('gear_qty')
            order_details['Quantity'] = str(gear_qty)

            gear_packaging = request.session.get('gear_packaging')
            if gear_packaging:
                order_details['packaging'] = gear_packaging

            gear_brew_method = request.session.get('gear_brew_method')
            if gear_brew_method:
                order_details['brew_method'] = gear_brew_method

            price = gear.price * int(gear_qty)

            voucher = None
            gear_voucher = request.session.get('gear_voucher')
            if gear_voucher:
                try:
                    voucher = (
                        Voucher.objects.filter(mode=True, category__name='GiftSets')
                                       .get(name=gear_voucher))
                except Voucher.DoesNotExist:
                    voucher = None
                else:
                    price -= price * voucher.discount / 100 + voucher.discount2
                    # Mark voucher as used for current customer
                    customer.vouchers.add(voucher)
                    customer.save()
                    voucher.count += 1
                    voucher.save()

            # pre-order
            # if (now.month == 1 and now.day < 9):
            #     order_details['Pre-Order'] = 'True'
            #     shipping_date = datetime(
            #         2017, 1, 9,
            #         hour=12, minute=0, second=0, microsecond=0,
            #         tzinfo=timezone.get_current_timezone())
            # else:
            #     shipping_date = get_shipping_date()

            shipping_date = get_shipping_date()

            # create order but do not save it until payment
            order = GearOrder(
                customer=customer,
                gear=gear,
                date=now,
                shipping_date=shipping_date,
                price=price,
                details=order_details,
                voucher=voucher,
            )
            print "order created but not saved:", order


            data = {
                'christmas-gift': order.gear.name,
                'price': order.price,
                'voucher': voucher.name if voucher else ''
            }

            # charge client
            result = charge_stripe(request, customer.stripe_id, order.price, metadata=data)
            if result.get('paid') and result.get('status') == 'succeeded':
                data['charge'] = result.get('charge_id')

                add_event.delay(
                    customer_id=customer.id,
                    event='christmas-gift-charge',
                    data=data,
                )

                # save paid order
                order.save()

                # TODO
                # send_email_async.delay(
                #     subject='Order Confirmation',
                #     template='OF 1 - Customer purchase one-offs (done)',
                #     to_email=customer.get_email(),
                #     from_email='Ernest from Hook Coffee <hola@hookcoffee.com.sg>',
                #     merge_vars={
                #         'USERNAME': customer.first_name,
                #         'COFFEE': ', '.join(['{} (x{})'.format(x[0], x[1]) for x in coffee_names]),
                #         'PRICE': '{:.2f} SGD'.format(request.session.get('stripe_amount', 0) / 100.),
                #         'SHIPPING_DATE': datetime.strftime(order.shipping_date, '%d/%m/%y'),
                #         'DOMAIN_NAME': request.META.get('HTTP_HOST'),
                #     }
                # )


            add_event.delay(
                customer_id=customer.id,
                event='signed-up-christmas',
                data={'credits': round(customer.amount, 2)})

            add_event.delay(
                customer_id=customer.id,
                event='buy-christmas-gift',
                data={
                    'gear-order': order.id,
                })

            new_user = authenticate(
                email=user.email,
                password=request.session['password'])
            login(request, new_user)

            if gear_color_id:
                gear_imgs = gear.images.filter(color=gear_color_id)
            else:
                gear_imgs = gear.images

            context = {
                'gear': gear.name,
                'image': gear_imgs.first().image.url if gear_imgs else "",
                'order_price': order.price,
                'token': get_token(request),
                'order_id': order.id,
            }

            # update campaign status to subscribed if from a campaign
            # Order != GearOrder
            # mailing_list.update_mailchimp_tracking(request, order, MailchimpCampaignStats.PURCHASED)

            return JsonResponse(context)

        return JsonResponse(result)

    else:
        rf = CustomRegistrationForm(prefix='one')
        cf = GS_CustomerForm(prefix='two')
        pf = GS_PreferencesForm(prefix='tri')
        new_gift_address_form = GiftAddressForm()

        f = forms.IntegerField()
        gear = CoffeeGear.objects.get(id=f.clean(request.session['gear_id']))
        gear_qty = f.clean(request.session['gear_qty'])

        total_price = gear.price * gear_qty
        gear_voucher = request.session.get('gear_voucher')
        if gear_voucher:
            try:
                voucher = (
                    Voucher.objects.filter(mode=True, category__name='GiftSets')
                                   .get(name=gear_voucher))
            except Voucher.DoesNotExist:
                voucher = None
            else:
                total_price -= total_price * voucher.discount / 100 + voucher.discount2

    af = AuthenticationForm(prefix='four')

    context = {
        'reg_form': rf,
        'cus_form': cf,
        'pre_form': pf,
        'gear': gear,
        'gear_qty': gear_qty,
        'total_price': total_price,
        'stripe_key': settings.PUBLISHABLE_KEY,
        'new_gift_address_form': new_gift_address_form,
        'show_login_form': True,
        'auth_form': af,
    }
    return render(request, 'get_started/registration-gear.html', context)


def _get_intro_form(request, context):
    form = GetStartedResponseForm(request.POST)

    if form.is_valid():
        name = form.cleaned_data['name']
        email = form.cleaned_data['email']

        try:
            exists = MyUser.objects.get_by_natural_key(email)
        except:
            exists = False

        if exists:
            context['errors'] = 'Email registered already.'

        else:
            form.save(commit=True)

            now = CTZ.normalize(timezone.now())

            # mark previous reminders (from Get Started) as completed
            Reminder.objects.filter(email__iexact=email).update(completed=True)
            for reminder in Reminder.objects.filter(email__iexact=email):
                reminder.disable_voucher()

            personal_voucher = None

            # 2 hours after customer entered name and email but haven’t signed up
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Sam from Hook Coffee <hola@hookcoffee.com.sg>',
                subject="{}, can I help?".format(name.title()),
                template_name=settings.REACTIVATION_TEMPLATES[0],
                scheduled=now + timedelta(hours=2),
                voucher=personal_voucher
            )

            # 1 day after customer entered name and email but haven’t signed up
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Ernest from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='Let the quality of our coffee speak for itself',
                template_name=settings.REACTIVATION_TEMPLATES[1],
                scheduled=now + timedelta(days=1),
                voucher=personal_voucher
            )

            # 2 days after customer entered name and email but haven’t signed up
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Kit from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='A free coffee gift from me to you..',
                template_name=settings.REACTIVATION_TEMPLATES[2],
                scheduled=now + timedelta(days=2),
                voucher=personal_voucher
            )

            # 4 days after customer entered name and email but haven’t signed up
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Kit from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='{}, your FREE V60 dripper is waiting for you'.format(name.title()),
                template_name=settings.REACTIVATION_TEMPLATES[3],
                scheduled=now + timedelta(days=4),
                voucher=personal_voucher
            )

            context['valid'] = True
            context['username'] = name
            context['email'] = email

            # if accesstoken exists, call FB api and save user info to db
            if request.POST['accesstoken']:
                accesstoken = request.POST['accesstoken']

                # data from Facebook that will be pulled out, minus 'user_about_me'
                request_data = 'first_name,last_name,email,gender,id'

                response = requests.get('https://graph.facebook.com/me?access_token=' + accesstoken + '&fields=' + request_data)
                # response.encoding = 'ISO-8859-1'
                # all requested user's data is here
                response_data = response.json()

                request.session['name'] = name
                request.session['accesstoken'] = accesstoken
                request.session['email'] = response_data['email']

                try:
                    FacebookCustomer.objects.create(
                        first_name=response_data['first_name'],
                        last_name=response_data['last_name'],
                        email=response_data['email'],
                        gender=response_data['gender'],
                        customer=None,
                        facebook_id=response_data['id']
                    )
                    request.session['accesstoken'] = accesstoken
                    logger.debug('FacebookCustomer created: %s', request.session['email'])
                except Exception:
                    email = request.session['email']
                    logger.error(
                        'FacebookCustomer not created: %s', email,
                        extra={'data': {
                            'fb_email': email,
                            'form_email': form.cleaned_data['email']
                        }},
                        exc_info=True)
            else:
                request.session['name'] = name
                request.session['email'] = email
                sys.stderr.write('No accesstoken. User did not login using FB')
    return form


def _load_session(request, gs_response):
    logger.debug(
        'Load last session: %s; response id: %s; current session: %s',
        gs_response.email, gs_response.id, get_session_data(request))
    request.session['name'] = gs_response.name
    request.session['email'] = gs_response.email
    request.session['default_pack'] = gs_response.form_details['default_pack']
    request.session['brew_title'] = gs_response.form_details['brew_title']
    ref = gs_response.form_details.get('ref')
    accesstoken = gs_response.form_details.get('accesstoken')
    if ref:
        request.session['ref'] = ref
    if accesstoken:
        request.session['accesstoken'] = accesstoken
    request.session['coffee'] = gs_response.ct_id
    # request.session['chosen_voucher'] = gs_response.form_details['chosen_voucher']  # no need?
    logger.debug(
        'Session was loaded: %s; response id: %s; new session: %s',
        gs_response.email, gs_response.id, get_session_data(request))


@json_view
@geo_check
def register_worldwide(request, is_worldwide):
    cart_list = request.session.get('shopping-cart', [])
    coffee_cost = Decimal(0)
    orders = []
    overall_qty = 0
    for cart_item in cart_list:
        quantity = int(cart_item.get('quantity', 0))
        if cart_item.get('coffee') and quantity > 0:
            try:
                coffee = CoffeeType.objects.get(id=cart_item.get('coffee').get('id'))
                coffee_cost += coffee.amount_one_off * quantity
                orders.append((coffee.name, quantity))
                overall_qty += quantity
            except CoffeeType.DoesNotExist:
                pass
        elif cart_item.get("workshop") and quantity > 0:
            try:
                workshop = WorkShops.objects.get(id=cart_item.get('workshop').get('id'))
                coffee_cost += workshop.cost * quantity
                orders.append((workshop.name, quantity, cart_item.get('workshop').get("date")))
                overall_qty += quantity
            except WorkShops.DoesNotExist:
                logger.info("WorkShop Doesn't Exist!")
        elif cart_item.get('gear') and quantity > 0:
            try:
                gear = CoffeeGear.objects.get(id=cart_item.get('gear').get('id'))
                coffee_cost += gear.price * quantity
                orders.append((gear.name, quantity))
                overall_qty += quantity
            except CoffeeGear.DoesNotExist:
                pass

    request.session['coffee_cost'] = float(coffee_cost)

    if request.method == "POST":
        result = {}
        email = request.session.get('email')
        now = CTZ.normalize(timezone.now())

        if 'one-password1' in request.POST:
            rf = CustomRegistrationForm(request.POST, prefix='one')
            if rf.is_valid():
                result['success'] = True
                request.session['email'] = rf.cleaned_data['email']
                request.session['password'] = request.POST.get('one-password1')
                mailchimp_subscribe.delay(email=request.session.get('email'))
            else:
                return HttpResponse(json.dumps(rf.errors))

        if 'two-first_name' in request.POST:
            cf = GS_CustomerForm(request.POST, prefix='two')
            pf = GS_PreferencesForm(request.POST, prefix='tri')

            if cf.is_valid():
                result['success'] = True
                request.session['first_name'] = request.POST.get('two-first_name')
                request.session['last_name'] = request.POST.get('two-last_name')
                request.session['country'] = request.POST.get('two-country', 'SG')
                request.session['line1'] = request.POST.get('two-line1')
                request.session['line2'] = request.POST.get('two-line2')
                request.session['postcode'] = request.POST.get('two-postcode')
                request.session['phone'] = request.POST.get('two-phone')
                mailchimp_subscribe.delay(
                    email=email,
                    merge_vars={
                        'FNAME': request.session.get('first_name'),
                        'LNAME': request.session.get('last_name'),
                    },
                )
            else:
                return HttpResponse(json.dumps(cf.errors))

        if 'confirm' in request.POST:
            try:
                user = MyUser(email=email)
                user.set_password(request.session.get('password'))
                user.save()
                logger.debug('User created: %s', user)
            except Exception:
                logger.error(
                    'User not created: %s', email, exc_info=True)

            try:
                card_details = '{}{}{}'.format(request.session.get('last4'),
                                                 '{:0>2}'.format(request.session.get('exp_month')),
                                                 request.session.get('exp_year'))
                customer = Customer.objects.create(
                    user=user,
                    first_name=request.session.get('first_name'),
                    last_name=request.session.get('last_name'),
                    amount=0,
                    country=request.session.get('country'),
                    line1=request.session.get('line1'),
                    line2=request.session.get('line2'),
                    postcode=request.session.get('postcode'),
                    phone=request.session.get('phone').strip(),
                    stripe_id=request.session.get('stripe_id'),
                    card_details=card_details.strip()
                )
                logger.debug('Customer created: %s', customer)
            except Exception:
                logger.error(
                    'Customer not created: %s', email, exc_info=True)

            logger.debug(
                'GLOBAL REGISTRATION. Confirmation: %s [%s] Customer: %s',
                request.user, get_client_ip(request), {
                    'customer': customer,
                    'country': customer.country
                })

            if customer.country == 'SG':
                is_singaporean = True
                # template_name = 'get_started/thankyou.html'
            else:
                is_singaporean = False
                # template_name = 'get_started/thanks-worldwide.html'

            preferences = Preferences(customer=customer)
            preferences.brew = BrewMethod.objects.get(name='None')

            try:
                voucher = Voucher.objects.get(name=request.session.get('voucher'))
                # TODO save if payment succeeded only
                voucher.count += 1
                voucher.save()
                # TODO save if payment succeeded only
                customer.vouchers.add(voucher)
                customer.save()
            except Voucher.DoesNotExist:
                voucher = None

            cart_list = request.session.get('shopping-cart')
            coffee_names = []
            temp_orders = []
            calendar_orders = []
            overall_amount = overall_weight = total = discount_part = 0

            for cart_item in cart_list:
                if vouchers_allowed(cart_item):
                    item_count = int(cart_item.get('quantity', 0))
                    total += item_count

            if voucher and total:
                discount_part = Decimal(voucher.discount2) / total

            shipping_cost = shipping_cost_bottled = 0

            for cart_item in cart_list:
                quantity = int(cart_item.get('quantity', 0))
                if cart_item.get('coffee') and quantity > 0:
                    coffee = CoffeeType.objects.get(id=cart_item.get('coffee').get('id'))
                    if not preferences.coffee:
                        preferences.coffee = coffee
                        preferences.save()
                    price = coffee.amount_one_off - discount_part - coffee.amount_one_off * voucher.discount / 100 if voucher else coffee.amount_one_off
                    is_recurrent = False
                    brew_method = BrewMethod.objects.get(id=cart_item.get('coffee').get('brew_id'))
                    package = cart_item.get('coffee').get('package')
                    is_nespresso = coffee.brew_method.all()[0].name == 'Nespresso'
                    coffee_names.append((coffee.name, quantity))
                    shipping_date = get_shipping_date()
                    overall_amount += price * quantity
                    overall_weight += coffee.weight * quantity

                    if coffee.is_bottled():
                        for i in range(quantity):
                            shipping_cost_bottled += 10 if shipping_cost_bottled == 0 else 5

                    for j in range(quantity):
                        try:
                            order = createOrder(
                                p_customer=customer,
                                p_coffee=coffee,
                                p_shipping_date=shipping_date,
                                p_price=price,
                                p_is_recurrent=is_recurrent,
                                p_brew_method=brew_method,
                                p_package=package,
                                is_nespresso=is_nespresso,
                                p_preferences=preferences,
                                p_voucher=voucher
                            )
                            temp_orders.append(order)
                        except Exception:
                            logger.error(
                                'Order not created; customer: %s; coffee: %s',
                                customer, coffee, exc_info=True)
                            order = None

                elif cart_item.get('gear') and quantity > 0:
                    gear = CoffeeGear.objects.get(id=cart_item.get('gear').get('id'))
                    price = gear.price * int(quantity)
                    if voucher and vouchers_allowed(cart_item):
                        price -= discount_part * quantity + price * voucher.discount / 100
                    order_details = {
                        'Quantity': str(quantity)
                    }
                    coffee_names.append((gear.name, quantity))
                    overall_amount += price
                    overall_weight += gear.weight * quantity

                    if START_DATE <= now <= END_DATE and gear.special == 'christmas':
                        shipping_date = NEW_DATE
                    else:
                        shipping_date = get_shipping_date()

                    order = GearOrder(
                        customer=customer,
                        gear=gear,
                        shipping_date=shipping_date,
                        price=price,
                        details=order_details,
                        voucher=voucher,
                    )
                    temp_orders.append(order)
                    if gear.special == 'christmas':
                        calendar_orders.append((gear.name, quantity, price, order.shipping_date))

                elif cart_item.get('workshop') and quantity > 0:
                    workshop = WorkShops.objects.get(id=cart_item.get('workshop').get('id'))
                    price = workshop.cost * int(quantity)
                    if voucher and vouchers_allowed(cart_item):
                        price -= discount_part * quantity + price * voucher.discount / 100
                    coffee_names.append((workshop.name, quantity))
                    overall_amount += price
                    scheduled_date = cart_item.get("workshop").get("date")

                    order = WorkShopOrder(
                        customer=customer,
                        workshop=workshop,
                        scheduled_date=scheduled_date,
                        price=price,
                        count = quantity,
                        voucher=voucher,
                    )
                    temp_orders.append(order)

            if not is_singaporean:
                get_shipping_rates(request, cid=customer.country, overall_weight=overall_weight)
                shipping_cost = request.session.get('shipping_cost')
                overall_amount = float(overall_amount) + shipping_cost
            else:
                shipping_cost += shipping_cost_bottled
                overall_amount += shipping_cost_bottled

            data = {
                'coffees': ', '.join(['{} (x{})'.format(x[0], x[1]) for x in coffee_names]),
                'calendars': ', '.join(['{} (x{})'.format(x[0], x[1]) for x in calendar_orders]),
                'country': customer.country.code,
                'shipping-cost': shipping_cost,
                'overall-cost': float(overall_amount),
                'overall-weight': overall_weight,
                'voucher': voucher.name if voucher else ''
            }

            result = charge_stripe(request, customer.stripe_id, overall_amount, metadata=data)
            if result.get('paid') and result.get('status') == 'succeeded':
                data['charge'] = result.get('charge_id')

                add_event.delay(
                    customer_id=customer.id,
                    event='cart-charge',
                    data=data,
                )

                [x.save() for x in temp_orders]

                # send email only when there are not special (not Christmas) orders
                if not (calendar_orders and len(calendar_orders) == len(coffee_names)):
                    send_email_async.delay(
                        subject='Order Confirmation',
                        template='OF 1 - Customer purchase one-offs (done)',
                        to_email=customer.get_email(),
                        from_email='Ernest from Hook Coffee <hola@hookcoffee.com.sg>',
                        merge_vars={
                            'USERNAME': customer.first_name,
                            'COFFEE': ', '.join(['{} (x{})'.format(x[0], x[1]) for x in coffee_names]),
                            'PRICE': '{:.2f} SGD'.format(request.session.get('stripe_amount', 0) / 100.),
                            'SHIPPING_DATE': datetime.strftime(get_shipping_date(), '%d/%m/%y'),
                            'DOMAIN_NAME': request.META.get('HTTP_HOST'),
                        }
                    )

                # send separate email for special (Christmas) orders
                if calendar_orders:
                    order = calendar_orders[0]

                    address_name = "Base address"
                    line1 = customer.line1
                    country_postcode = "{} {}".format(customer.country, customer.postcode)

                    send_email_async.delay(
                        subject='Order Confirmation',
                        template='Christmas pre-order',
                        to_email=customer.get_email(),
                        from_email='Ernest from Hook Coffee <hola@hookcoffee.com.sg>',
                        merge_vars={
                            'USERNAME': customer.first_name,
                            'COFFEE': ''.join(['{} (x{})\t${}<br/>'.format(x[0], x[1], x[2]) for x in calendar_orders]),
                            'PRICE': 'S${:.2f}'.format(
                                sum([x[2] for x in calendar_orders])
                                ),
                            'SHIPPING_DATE': "{} {}".format(
                                    ordinal(order[3].day),
                                    datetime.strftime(order[3], '%B %Y'),
                                ),
                            'DOMAIN_NAME': request.META.get('HTTP_HOST'),
                            'ADDRESS_NAME': address_name,
                            'LINE1': line1,
                            'COUNTRY_POSTCODE': country_postcode,
                            'ESTIMATED_DELIVERY': get_estimated_date(order[3]),

                        }
                    )

                request.session['shopping-cart'] = []

            else:
                request.session['stripe-notification'] = result.get('error')
                if result.get('code') == 'card_declined':
                    request.session['stripe-notification'] = "Oops your card has been declined. Please try using another credit card."

            # TODO: create Referral code

            # TODO: mark all Reminders as completed

            # TODO: update campaign status to subscribed if came from a campaign

            new_user = authenticate(email=user.email,
                                    password=request.session.get('password'))
            login(request, new_user)


            request.session['active_tab'] = 'active_one_offs'

            return redirect('profile')

        return result
    else:
        rf = CustomRegistrationForm(prefix='one')
        af = AuthenticationForm(prefix='four')
        naf = AddressForm()
        context = {}

        if is_worldwide:
            cf = GS_CustomerForm(prefix='two')
        else:
            cf = GS_CustomerForm(prefix='two', initial={'country': 'SG'})

        pf = GS_PreferencesForm(prefix='tri')

        try:
            customer = Customer.objects.get(user=request.user)
        except:
            customer = None

        if customer:
            show_subscription_form = False
            show_login_form = False
            show_active_subs = False

            # get available addresses
            addresses = Address.objects.filter(customer=customer)
            addresses = [{
                'id': x.id,
                'name': x.name,
                'country': str(x.country),
                'line1': x.line1,
                'line2': x.line2,
                'postcode': x.postcode,
                'customer_name': '{} {}'.format(customer.first_name, customer.last_name),
            } for x in addresses]

            context['base_address'] = json.dumps({
                'id': -1,
                'country': str(customer.country),
                'line1': customer.line1,
                'line2': customer.line2,
                'postcode': customer.postcode,
                'customer_name': '{} {}'.format(customer.first_name, customer.last_name),
            })
            context['addresses'] = json.dumps(addresses)

        else:
            show_login_form = request.session.get('from_shopping_cart')
            show_subscription_form = not show_login_form
            show_active_subs = False
            context['addresses'] = []
            context['base_address'] = {}

        context.update({
            'is_worldwide': is_worldwide,
            'stripe_key': settings.PUBLISHABLE_KEY,
            'reg_form': rf,
            'cus_form': cf,
            'pre_form': pf,
            'auth_form': af,
            'new_address_form': naf,
            'cart_quantity': request.session.get('cart_quantity'),
            'coffee_cost': float(coffee_cost),
            'shipping_cost': request.session.get('shipping_cost', 0),
            'no_cart': True,
            'orders': orders,
            'country_name': request.session.get('country_name'),
            'show_login_form': show_login_form,
            'show_subscription_form': show_subscription_form,
            'show_active_subs': show_active_subs,
        })
        return render(request, 'get_started/registration-worldwide.html', context)


@geo_check
def cart_process(request, is_worldwide):
    """Process shopping cart and charge client."""
    # check where to ship order to
    addr_id = request.GET.get('addrId', -1)
    try:
        address = Address.objects.get(id=addr_id)
    except:
        # use base address
        address = None

    now = CTZ.normalize(timezone.now())
    customer = Customer.objects.get(user=request.user)
    cart_list = request.session.get('shopping-cart')
    coffee_cost = overall_amount = overall_weight = total \
        = discount_part = shipping_cost = shipping_cost_bottled = 0
    coffee_ids = []
    coffee_names = []
    temp_orders = []
    calendar_orders = []

    try:
        voucher = Voucher.objects.get(name=request.session.get('voucher'))
        # TODO save if payment succeeded only
        voucher.count += 1
        voucher.save()
        # TODO save if payment succeeded only
        customer.vouchers.add(voucher)
        customer.save()
    except Voucher.DoesNotExist:
        voucher = None

    for cart_item in cart_list:
        if vouchers_allowed(cart_item):
            item_count = int(cart_item.get('quantity', 0))
            total += item_count

    if voucher and total:
        discount_part = Decimal(voucher.discount2) / total

    for cart_item in cart_list:
        quantity = int(cart_item.get('quantity'))
        if cart_item.get('workshop') and quantity:
            workshop = WorkShops.objects.get(id=cart_item.get('workshop').get('id'))
            coffee_cost += workshop.cost * quantity
            price = workshop.cost - discount_part - workshop.cost * voucher.discount / 100 if voucher else workshop.cost
            shipping_date = get_shipping_date()
            overall_amount += price * quantity
            for j in range(quantity):
                try:
                    order = WorkShopOrder(
                        workshop=workshop,
                        customer=customer,
                        shipping_date=shipping_date,
                        scheduled_date=cart_item.get('workshop').get("date"),
                        price=price,
                        voucher=voucher,
                    )
                    if address:
                        order.address = address
                    temp_orders.append(order)
                except Exception:
                    order = None

        elif cart_item.get('coffee') and quantity > 0:
            try:
                coffee = CoffeeType.objects.get(id=cart_item.get('coffee').get('id'))
                brew_method = BrewMethod.objects.get(id=cart_item.get('coffee').get('brew_id'))
                package = cart_item.get('coffee').get('package')
                price = coffee.amount_one_off - discount_part - coffee.amount_one_off * voucher.discount / 100 if voucher else coffee.amount_one_off
                is_nespresso = coffee.brew_method.all()[0].name == 'Nespresso'

                coffee_ids.append({'id':coffee.id, 'qty':quantity})
                coffee_names.append((coffee.name, quantity, price))

                shipping_date = get_shipping_date()

                overall_amount += price * quantity
                overall_weight += coffee.weight * quantity

                if coffee.is_bottled():
                    for i in range(quantity):
                        shipping_cost_bottled += 10 if shipping_cost_bottled == 0 else 5

                for j in range(quantity):
                    try:
                        order = createOrder(
                            p_customer=customer,
                            p_coffee=coffee,
                            p_shipping_date=shipping_date,
                            p_price=price,
                            p_is_recurrent=False,
                            p_brew_method=brew_method,
                            p_package=package,
                            is_nespresso=is_nespresso,
                            p_preferences=customer.preferences,
                            p_voucher=voucher,
                        )
                        if address:
                            order.address = address
                        temp_orders.append(order)
                        coffee_cost += order.amount
                    except Exception:
                        order = None
            except Exception:
                logger.error('Failed to parse coffee item: %s',
                             cart_item.get('coffee'), exc_info=True)

        elif cart_item.get('gear') and quantity > 0:
            try:
                gear = CoffeeGear.objects.get(id=cart_item.get('gear').get('id'))
                price = gear.price * quantity
                if voucher and (vouchers_allowed(cart_item) or voucher.name == 'CHRISTMAS10'):
                    price -= discount_part * quantity + price * voucher.discount / 100
                order_details = {
                    'Quantity': str(quantity)
                }

                coffee_names.append((gear.name, quantity, price))
                overall_amount += price
                overall_weight += gear.weight * quantity

                if START_DATE <= now <= END_DATE and gear.special == 'christmas':
                    shipping_date = NEW_DATE
                else:
                    shipping_date = get_shipping_date()

                order = GearOrder(
                    customer=customer,
                    gear=gear,
                    shipping_date=shipping_date,
                    price=price,
                    details=order_details,
                    voucher=voucher,
                )
                temp_orders.append(order)
                if address:
                    order.address = address
                if gear.special == 'christmas':
                    calendar_orders.append((gear.name, quantity, price, shipping_date))

            except Exception:
                logger.error('Failed to parse coffee item: %s',
                             cart_item.get('coffee'), exc_info=True)

    if customer.country != 'SG':
        get_shipping_rates(request, cid=customer.country, overall_weight=overall_weight)
        shipping_cost = request.session.get('shipping_cost')
        overall_amount = float(overall_amount) + shipping_cost
    else:
        shipping_cost += shipping_cost_bottled
        overall_amount += shipping_cost_bottled

    data = {
        'coffees': ', '.join(['{} (x{})'.format(x[0], x[1]) for x in coffee_names]),
        'calendars': ', '.join(['{} (x{})'.format(x[0], x[1]) for x in calendar_orders]),
        'country': customer.country.code,
        'shipping-cost': shipping_cost,
        'overall-cost': float(overall_amount),
        'overall-weight': overall_weight,
    }

    result = charge_stripe(request, customer.stripe_id, overall_amount, metadata=data)

    if result.get('paid') and result.get('status') == 'succeeded':
        data['charge'] = result.get('charge_id')

        add_event.delay(
            customer_id=customer.id,
            event='cart-charge',
            data=data,
        )

        [x.save() for x in temp_orders]

        if order.address:
            address_name = order.address.name
            line1 = order.address.line1
            country_postcode = "{} {}".format(order.address.country, order.address.postcode)
        else:
            address_name = "Base address"
            line1 = customer.line1
            country_postcode = "{} {}".format(customer.country, customer.postcode)

        try:
            referral = Referral.objects.get(user=customer.user)
        except Referral.DoesNotExist:
            referral_code = None
        else:
            referral_code = referral.code

        # send email only when there are not special (not Christmas) orders
        if not (calendar_orders and len(calendar_orders) == len(coffee_names)):
            send_email_async.delay(
                subject='Your order has been confirmed',
                template='EJ4',
                to_email=customer.get_email(),
                from_email='Sam from Hook Coffee <hola@hookcoffee.com.sg>',
                merge_vars={
                    'USERNAME': customer.first_name,
                    'COFFEE': ', '.join(['{} (x{})'.format(x[0], x[1]) for x in coffee_names]),
                    'COFFEE2': ''.join(['{} (x{})\t${}<br/>'.format(x[0], x[1], x[2]) for x in coffee_names]),
                    'PRICE': 'S${:.2f}'.format(request.session.get('stripe_amount', 0) / 100.),
                    'SHIPPING_DATE': "{} {}".format(
                        ordinal(order.shipping_date.day),
                        datetime.strftime(order.shipping_date, '%B %Y'),
                    ),
                    'ADDRESS_NAME': address_name,
                    'LINE1': line1,
                    'COUNTRY_POSTCODE': country_postcode,
                    'ESTIMATED_DELIVERY': get_estimated_date(order.shipping_date),
                    'REFERRAL_CODE': referral_code,
                    'DOMAIN_NAME': request.META.get('HTTP_HOST'),
                }
            )

        # send separate email for special (Christmas) orders
        if calendar_orders:
            order = calendar_orders[0]

            address_name = "Base address"
            line1 = customer.line1
            country_postcode = "{} {}".format(customer.country, customer.postcode)

            send_email_async.delay(
                subject='Order Confirmation',
                template='Christmas pre-order',
                to_email=customer.get_email(),
                from_email='Ernest from Hook Coffee <hola@hookcoffee.com.sg>',
                merge_vars={
                    'USERNAME': customer.first_name,
                    'COFFEE': ''.join(['{} (x{})\t${}<br/>'.format(x[0], x[1], x[2]) for x in calendar_orders]),
                    'PRICE': 'S${:.2f}'.format(
                        sum([x[2] for x in calendar_orders])
                        ),
                    'SHIPPING_DATE': "{} {}".format(
                            ordinal(order[3].day),
                            datetime.strftime(order[3], '%B %Y'),
                        ),
                    'DOMAIN_NAME': request.META.get('HTTP_HOST'),
                    'ADDRESS_NAME': address_name,
                    'LINE1': line1,
                    'COUNTRY_POSTCODE': country_postcode,
                    'ESTIMATED_DELIVERY': get_estimated_date(order[3]),

                }
            )

        new_purchase_amount = float(request.session.get('stripe_amount', 0) / 100.)
        request.session['new_purchase_amount'] = new_purchase_amount

        # not sending reminders for abandoned cart
        try:
            ShoppingCart.objects.get(customer=customer).delete()
        except:
            pass

        request.session['shopping-cart'] = []

    else:
        request.session['stripe-notification'] = result.get('error')
        if result.get('code') == 'card_declined':
            request.session['stripe-notification'] = "Oops your card has been declined. Please try using another credit card."


    request.session['active_tab'] = 'active_one_offs'
    request.session['voucher'] = ""

    return redirect('profile')


@require_POST
@json_view
def login_existing_user(request):
    form = AuthenticationForm(data=request.POST or None, prefix='four')
    if form.is_valid():
        email = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(
            email=email,
            password=password)
        # try:
        #     user = MyUser.objects.get(email=email)
        # except MyUser.DoesNotExist:
        #     return {'errors': 'Check email address and password again'}
        login(request, user)
        try:
            customer = Customer.objects.get(user=user)
        except Customer.DoesNotExist:
            customer = None

        if customer:
            base_address = {
                'id': -1,
                'country': str(customer.country),
                'line1': customer.line1,
                'line2': customer.line2,
                'postcode': customer.postcode,
                'customer_name': '{} {}'.format(customer.first_name, customer.last_name),
            }
            addresses = Address.objects.filter(customer=customer)
            addresses = [{
                'id': x.id,
                'name': x.name,
                'country': str(x.country),
                'line1': x.line1,
                'line2': x.line2,
                'postcode': x.postcode,
                'customer_name': '{} {}'.format(customer.first_name, customer.last_name),
            } for x in addresses]

            if request.session.get('from_preregister'):
                coffee = CoffeeType.objects.get(id=request.session.get('coffee'))

                nespresso = BrewMethod.objects.get(name='Nespresso')
                is_pods = False
                if nespresso in coffee.brew_method.all():
                    is_pods = True
                all_active_subscriptions = Order.objects.filter(
                    customer=customer,
                    status=Order.ACTIVE,
                    recurrent=True
                )
                active_subscriptions = [(x.id, x.coffee.name, x.coffee.img.url, x.address.name if x.address else 'Base address')\
                    for x in all_active_subscriptions
                    if (nespresso in x.coffee.brew_method.all()) == is_pods]

                return {
                    'active_subscriptions': json.dumps(active_subscriptions),
                    'token': get_token(request),
                    'base_address': base_address,
                    'addresses': addresses,
                }

            elif request.session.get('from_shopping_cart'):
                return {
                    'prepare_cart': True,
                    'base_address': base_address,
                    'addresses': addresses,
                    'token': get_token(request),
                }

    else:
        return {'errors': 'Check email address and password'}
        # return {'errors': form.errors}

    return redirect('profile')


@require_POST
@json_view
def login_customer(request):
    print "login_customer"
    form = AuthenticationForm(data=request.POST or None, prefix='four')
    if form.is_valid():
        email = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(
            email=email,
            password=password)
        login(request, user)

        try:
            customer = Customer.objects.get(user=user)
        except Customer.DoesNotExist:
            customer = None
    else:
        return JsonResponse({'errors': form.errors})

    return JsonResponse({'success': True})


@require_POST
def substitute_subscription(request):
    dest_order = request.POST.get('dest-order', 0)
    goal_coffee_id = request.POST.get('goal-coffee-id', 0)

    try:
        order = Order.objects.get(id=dest_order)
        coffee = CoffeeType.objects.get(id=goal_coffee_id)
    except Order.DoesNotExist:
        order = None
    except CoffeeType.DoesNotExist:
        coffee = None
    else:
        price = coffee.amount if order.recurrent else coffee.amount_one_off
        if order.voucher:
            price -= price * order.voucher.discount / 100 + order.voucher.discount2

        order.coffee = coffee
        order.amount = price
        order.save()

        add_event.delay(
            customer_id=order.customer_id,
            event='update-subscription',
            order_id=order.id)
    return redirect('profile')


@require_POST
@json_view
def add_subscription(request):
    """Add a subscription to logged in user.

    subParams  -- subscription parameters (package, interval, different, brew)
    coffeeID   -- subscription coffee id
    addrID     -- shipping address id
    """

    response = {
        'status': 'success',
    }
    customer = request.user.customer
    sub_params = json.loads(request.POST.get('subParams'))
    coffee_id = request.POST.get('coffeeID')
    addr_id = request.POST.get('addrID')

    try:
        interval = int(sub_params.get('interval'))
    except ValueError:
        interval = customer.preferences.interval

    try:
        brew_method = BrewMethod.objects.get(id=sub_params.get('brew'))
    except BrewMethod.DoesNotExist:
        brew_method = customer.preferences.brew

    try:
        coffee = CoffeeType.objects.get(id=coffee_id)
        amount = coffee.amount
    except CoffeeType.DoesNotExist:
        coffee = None
        response['status'] = 'failed'

    try:
        address = Address.objects.get(id=addr_id)
    except Address.DoesNotExist:
        address = None

    try:
        voucher = Voucher.objects.get(name=request.session.get("voucher", ""))
        amount -= amount * voucher.discount / 100 + voucher.discount2
        customer.vouchers.add(voucher)
        customer.save()
    except:
        voucher = None

    if coffee:
        order = Order.objects.create(
            customer=customer,
            coffee=coffee,
            date=timezone.now(),
            shipping_date=get_shipping_date(),
            amount=amount,
            interval=interval,
            recurrent=True,
            status=Order.ACTIVE,
            brew=brew_method,
            package=sub_params.get('package'),
            different=sub_params.get('different'),
            address=address,
            voucher=voucher,
        )

        add_event.delay(
            customer_id=order.customer_id,
            event='created-subscription',
            order_id=order.id)

        if voucher:
            voucher.increment()
            if voucher.name == 'AEROPRESS25':
                order.details[voucher.name] = True
                order.save()

        new_purchase_amount = float(amount)
        request.session['new_purchase_amount'] = new_purchase_amount
    else:
        response['status'] = 'failed'

    return response


def ordinal(n):
    if 10 <= n % 100 < 20:
        return str(n) + 'th'
    else:
        return  str(n) + {1 : 'st', 2 : 'nd', 3 : 'rd'}.get(n % 10, "th")
