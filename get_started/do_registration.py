# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import logging
import sys
from datetime import datetime, timedelta

import pytz

import stripe

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import ugettext as _

from coffees.models import BrewMethod, CoffeeType, Flavor

from customauth.models import MyUser

from customers.forms import AddressForm, GS_CustomerForm, GS_PreferencesForm
from customers.models import (
    Address, Customer, Order, Preferences, Reference, Referral, Voucher)
from customers.models.facebook_customer import FacebookCustomer
from customers.tasks import add_event, add_tag, mailchimp_subscribe
from customers.views import get_shipping_date

from get_started.forms import CustomRegistrationForm
from get_started.helpers import createOrder, generate_securerandompass
from get_started.models import GetStartedResponse, ReferralVoucher

from giveback_project.helpers import (
    get_client_ip, get_estimated_date, get_session_data)

from loyale.mixin import POINTS_FOR_INVITED_FRIEND, PointMixin

from manager import mailing_list
from manager.models import MailchimpCampaignStats

from reminders.models import Reminder, ReminderSMS


stripe.api_key = settings.SECRET_KEY
point_mixin = PointMixin()
logger = logging.getLogger('giveback_project.' + __name__)

GIFT_DISPLAY_NAMES = settings.GIFT_DISPLAY_NAMES
CTZ = timezone.get_current_timezone()

# CNY christmas
START_DATE = datetime(2018, 1, 14, 0, 0, 0, tzinfo=CTZ)
END_DATE = datetime(2018, 1, 28, 0, 0, 0, tzinfo=CTZ)
NEW_DATE = datetime(2018, 1, 29, 0, 0, 0, tzinfo=CTZ)


# abstracts out registration to prevent repeated code
def do_registration(request, is_nespresso):
    now = CTZ.normalize(timezone.now())

    result = context = {}

    isBottled = request.session.get('isBottled')

    if request.method == "POST":
        email = request.session.get('email')

        if 'one-password1' in request.POST:
            rf = CustomRegistrationForm(request.POST, prefix='one')
            if rf.is_valid():
                result['success'] = True

                details = json.loads(request.POST.get('array'))

                logger.debug(
                    'Registration: first step: %s; details: %s', email, details)

                request.session['email'] = rf.cleaned_data['email']
                request.session['password'] = generate_securerandompass(64) if 'accesstoken' in request.session \
                    else request.POST['one-password1']
                request.session['brew'] = details['brew']
                request.session['package'] = details['package']
                request.session['interval'] = details['interval']
                request.session['different'] = details['different']

                mailchimp_subscribe.delay(email=request.session.get('email'))
            else:
                return HttpResponse(json.dumps(rf.errors))

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
                return HttpResponse(json.dumps(cf.errors))

        if 'voucher' in request.POST:
            try:
                user = MyUser(email=request.session['email'])
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
                    stripe_id=request.session['stripe_id'],
                    card_details='{}{}{}'.format(
                        request.session.get('last4'),
                        '{:0>2}'.format(
                            request.session.get('exp_month')),
                        request.session.get('exp_year')
                    ))
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
                    preferences.coffee = coffee = CoffeeType.objects.get(id=request.session.get('coffee', response.ct))
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

            preferences.interval = int(request.session['interval'])
            preferences.interval_pods = int(request.session['interval'])
            preferences.different = True if request.session['different'] else False
            preferences.different_pods = True if request.session['different'] else False
            if is_nespresso:
                preferences.brew = BrewMethod.objects.get(name_en='None')
                preferences.package = Preferences.DRIP_BAGS
            else:
                try:
                    if response:
                        brew = BrewMethod.objects.get(id=response.form_details['method'])
                    else:
                        brew_id = request.session.get('brew')
                        if brew_id:
                            brew = BrewMethod.objects.get(id=brew_id)
                        else:
                            brew_title = request.session.get('brew_title') or _('None')
                            brew = BrewMethod.objects.get(name=brew_title)
                    preferences.brew = brew
                except Exception:
                    brew_title = request.session.get('brew_title') or _('None')
                    brew = BrewMethod.objects.get(name=brew_title)
                    preferences.brew = brew
                preferences.package = request.session['package']
            preferences.save()

            # common voucher
            try:
                voucher = Voucher.objects.get(name=request.session.get('voucher'))
                price -= price * voucher.discount / 100 + voucher.discount2

                # Mark voucher as used for current customer
                customer.vouchers.add(voucher)
                customer.save()
                voucher.count += 1
                voucher.save()
            except:
                voucher = None

            try:
                # referral voucher
                referral_voucher = ReferralVoucher.objects.get(code=request.session.get('referral_voucher'))
                price -= price * referral_voucher.discount_percent / 100 + referral_voucher.discount_sgd

                referral_voucher.used = True
                referral_voucher.save()
            except Exception:
                referral_voucher = None

            if request.session.get('alacarte') or \
                    request.session.get('gift'):
                is_recurrent = False
            else:
                is_recurrent = True

            if START_DATE <= now <= END_DATE:
                shipping_date = NEW_DATE
            else:
                shipping_date = get_shipping_date()

            if isBottled:
                brew_method = BrewMethod.objects.get(name_en='Cold Brew')
                preferences.brew = brew_method
                preferences.package = Preferences.BOTTLED
                preferences.different = False
                preferences.save()
            elif is_nespresso:
                brew_method = BrewMethod.objects.get(name_en='Nespresso')
            else:
                try:
                    brew_method = BrewMethod.objects.get(id=request.session['brew'])
                    preferences.brew = brew_method
                    preferences.save()
                except Exception:
                    brew_method = preferences.brew
            try:
                order = createOrder(
                    p_customer=customer,
                    p_coffee=coffee,
                    p_shipping_date=shipping_date,
                    p_price=price,
                    p_preferences=preferences,
                    p_is_recurrent=is_recurrent,
                    p_brew_method=brew_method,
                    p_voucher=voucher,
                    p_package=preferences.package,
                    is_nespresso=is_nespresso
                )
                order.save()

                if voucher:
                    if voucher.name in settings.GIFT_VOUCHERS:
                        order.details[voucher.name] = True
                        order.save()

                if referral_voucher:
                    order.details['referred_by'] = '{} {}'.format( \
                        referral_voucher.sender.first_name, referral_voucher.sender.last_name)
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

            if not request.session.get('active_tab') and is_nespresso:
                request.session['active_tab'] = 'active_subscriptions_pods'

            # Create referral code for new user
            Referral.objects.create(
                user=user,
                code=Referral.get_random_code(customer=customer)
            )

            # Use referral link
            ref = request.session.get('ref')
            if ref or referral_voucher:
                referrer = user
                if ref:
                    referred = Referral.objects.get(code=ref).user
                else:
                    referred = referral_voucher.sender.user
                Reference.objects.create(referrer=referrer, referred=referred)
                logger.debug('Reference created: %s <-- %s', referred, referrer)

                current_customer = referred.customer
                add_event.delay(
                    customer_id=current_customer.id,
                    event='reference-created',
                    data={'referred': referred.email,
                          'referrer': referrer.email})
                referrer_customer = Customer.objects.get(user_id=referrer.id)
                add_event.delay(
                    customer_id=referrer_customer.id,
                    event='reference-created',
                    data={'referred': referred.email,
                          'referrer': referrer.email})

                # add %50 discount to customer's available discounts
                referrals = json.loads(referred.customer.discounts['referral'])
                new_discount = (50, timezone.now().strftime('%Y-%m-%dT%H:%M:%S%z'))
                referrals.append(new_discount)
                referred.customer.discounts['referral'] = referrals
                referred.customer.save()

                add_event.delay(
                    customer_id=current_customer.id,
                    event='give-$50-to-referrer',
                    data={
                        'discount': new_discount[0],
                        'date': new_discount[1]
                    })

                cnt = Reference.objects.filter(referred=referred).count()
                if cnt == 2:
                    try:
                        current_order = Order.objects \
                            .filter(customer=current_customer) \
                            .filter(status__in=['AC', 'PA']) \
                            .latest('date')
                        current_order.details['KeepCup'] = True
                        current_order.save()
                    except Order.DoesNotExist:
                        pass

            Reminder.objects.filter(email=user.email).update(completed=True)
            for reminder in Reminder.objects.filter(email__iexact=user.email):
                reminder.disable_voucher()

            new_user = authenticate(email=user.email,
                                    password=request.session['password'])
            login(request, new_user)

            context = {
                'coffee': coffee.name,
                'image': coffee.img.url,
                'order_price': order.amount if order else coffee.amount,
            }

            Reminder.objects.create(
                username="{} {}".format(customer.first_name.title(), customer.last_name.title()),
                email=customer.user.email,
                order=order,
                from_email='Ernest from Hook Coffee <hola@hookcoffee.com.sg>',
                subject="Ahoy, {}!".format(customer.first_name.title()),
                template_name='EJ1',
                # scheduled=now + timedelta(hours=1),
                scheduled=now + timedelta(minutes=1), # TODO: remove
                voucher=voucher
            )

            ReminderSMS.objects.create(
                customer=customer,
                # WARNING: actual message generated in tasks module
                message=ReminderSMS.MESSAGE % customer.first_name.title(),
                # will be replaced with sms schedule date on save
                scheduled=shipping_date,
            )

            # update campaign status to subscribed if from a campaign
            mailing_list.update_mailchimp_tracking(request, order, MailchimpCampaignStats.PURCHASED)

            request.session['voucher'] = ""

            new_purchase_amount = float(price)
            request.session['new_purchase_amount'] = new_purchase_amount

            return render(request, 'get_started/thankyou.html', context)
        return result

    else:
        username = email = coffee = default_pack = brew_title = voucher_name = ''
        price = 0
        data = {}
        render_data = {}
        logger.debug(
            'Registration:init:%s:%s',
            get_client_ip(request), get_session_data(request))

        if not request.session.get('from_shopping_cart'):
            try:
                data['username'] = request.session.get('name')
                data['email'] = request.session.get('email')
                default_pack = request.session.get('default_pack') \
                               or Preferences.WHOLEBEANS
                if request.session.get('V60STARTER'):
                    default_pack = Preferences.GRINDED
                brew_title = request.session.get('brew_title') or _('Espresso')

            except Exception:
                logger.error(
                    'Registration:init:%s:%s',
                    get_client_ip(request), get_session_data(request),
                    exc_info=True)

            # Check if it's registration by ref link without ReferralVoucher
            # for example by FB or [copy ref link and share your own way]
            ref_code = request.session.get('ref')
            if ref_code:
                try:
                    referral = Referral.objects.get(code=ref_code)
                except Referral.DoesNotExist:
                    pass
                else:
                    # If referral voucher doesn't exists - create and use it
                    ref_voucher, created = ReferralVoucher.objects.get_or_create(
                        sender=referral.user.customer,
                        recipient_email=request.session.get('email', ''),
                        defaults={
                            # 'discount_percent': 50,
                            'discount_sgd': 12,
                            'code': ReferralVoucher.get_random_code(size=8),
                        }
                    )
                    # If referral voucher created right now it means that
                    # customer didn't get points for inviting the friend
                    # (one of the methods above).
                    if created:
                        point_mixin.grant_points(
                            user=referral.user,
                            points=POINTS_FOR_INVITED_FRIEND)
                    request.session['chosen_voucher'] = ref_voucher.code

            try:
                coffee = CoffeeType.objects.get(id=request.session.get('coffee'))
                if request.session.get('alacarte'):
                    price = coffee.amount_one_off
                else:
                    price = coffee.amount
            except Exception:
                coffee = None

            try:
                voucher = Voucher.objects.get(name=request.session['voucher'])
                if voucher:
                    price -= price * voucher.discount / 100 + voucher.discount2
            except:
                pass

            try:
                referral_voucher = ReferralVoucher.objects.get(
                    code=request.session.get('referral_voucher'))
                if referral_voucher:
                    price -= price * referral_voucher.discount_percent / 100 + referral_voucher.discount_sgd
            except:
                pass

        brew_methods = BrewMethod.objects.sorted(~Q(name_en='Nespresso'))
        rf = CustomRegistrationForm(prefix='one', initial=data)
        cf = GS_CustomerForm(prefix='two')
        pf = GS_PreferencesForm(prefix='tri')
        af = AuthenticationForm(prefix='four')
        naf = AddressForm()

    show_login_form = request.session.get('from_preregister') and not request.user.is_authenticated
    show_active_subs = False
    show_subscription_form = False
    show_sub_details = False
    active_subscriptions = []
    if request.user.is_authenticated:
        customer = request.user.customer
        try:
            coffee = CoffeeType.objects.get(id=request.session.get('coffee'))
        except CoffeeType.DoesNotExist:
            coffee = None

        nespresso = BrewMethod.objects.get(name='Nespresso')
        is_pods = False
        if coffee != None:
            if nespresso in coffee.brew_method.all():
                is_pods = True

        all_active_subscriptions = Order.objects.filter(
            customer=customer,
            status=Order.ACTIVE,
            recurrent=True
        )
        active_subscriptions = [[x.id, x.coffee.name, x.coffee.img.url, x.address.name if x.address else 'Base address']\
            for x in all_active_subscriptions
            if ((nespresso in x.coffee.brew_method.all()) == is_pods and x.is_editable)]
        if len(active_subscriptions):
            show_active_subs = True
        else:
            show_sub_details = not (show_login_form and show_subscription_form and show_active_subs)

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

        render_data['base_address'] = json.dumps({
            'id': -1,
            'country': str(customer.country),
            'line1': customer.line1,
            'line2': customer.line2,
            'postcode': customer.postcode,
            'customer_name': '{} {}'.format(customer.first_name, customer.last_name),
        })
        render_data['addresses'] = json.dumps(addresses)
    else:
        show_subscription_form = not show_login_form
        render_data['addresses'] = []
        render_data['base_address'] = {}

    active_subscriptions = json.dumps(active_subscriptions)

    render_data['reg_form'] = rf
    render_data['cus_form'] = cf
    render_data['pre_form'] = pf
    render_data['auth_form'] = af
    render_data['new_address_form'] = naf
    render_data['coffee'] = coffee
    render_data['isNespresso'] = is_nespresso
    render_data['price'] = "{0:.0f}".format(price)
    render_data['brew_title'] = brew_title
    render_data['brew_methods'] = brew_methods
    render_data['alacarte'] = request.session.get('alacarte')
    render_data['isBottled'] = isBottled
    render_data['default_pack'] = default_pack
    render_data['shipping_date'] = get_shipping_date()
    render_data['stripe_key'] = settings.PUBLISHABLE_KEY
    render_data['show_login_form'] = show_login_form
    render_data['show_subscription_form'] = show_subscription_form
    render_data['show_active_subs'] = show_active_subs
    render_data['show_sub_details'] = show_sub_details
    render_data['active_subscriptions'] = active_subscriptions
    render_data['estimated_date'] = get_estimated_date

    return render(request, 'get_started/registration.html', render_data)
