# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import logging
import re
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_UP

from jsonview.decorators import json_view

import pytz

import stripe

from django_countries import countries

from django import forms
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic.list import ListView

from coffees.models import (
    BrewMethod, CoffeeGear, CoffeeGearColor, CoffeeType, SharedCoffeeSticker,
    FarmPhotos, WorkShops)

from customers.forms import PreferencesForm, GiftAddressForm
from customers.models import (
    Customer, GearOrder, Order, Preferences,
    Voucher, Address,)
from customers.tasks import add_event

from manager import mailing_list
from manager.models import MailchimpCampaignStats

from giveback_project.helpers import (
    geo_check, get_client_ip, get_interval, get_shipping_date)

from reminders.models import Reminder

from .shipping_zones import zone1, zone2, zone3


stripe.api_key = settings.SECRET_KEY
logger = logging.getLogger('giveback_project.' + __name__)

CTZ = timezone.get_current_timezone()

PACKAGE_MAPPER = {
  "GR": 'Ground (200g)',
  "WB": 'Wholebeans (200g)',
  "DR": 'Drip bags (x10)',
  "PODS": 'Shotpods (x 20)',
  "BO": '6 x (330ml) bottles pack'
}


@geo_check
def bags(request, is_worldwide):
    try:
        customer = Customer.objects.get(user=request.user)
        # User who has been registered without credit card but with credits by a friend
        # goes out of credits and should provide credit card details
        out_of_credits = customer.amount == 0 and not customer.stripe_id
    except:
        out_of_credits = False

    coffee_list = CoffeeType.objects.bags()
    brew_methods = BrewMethod.objects.sorted(~Q(name_en__in=['None', 'Nespresso', 'Bottled',]))
    brew_methods_oneoff = BrewMethod.objects.sorted(~Q(name_en__in=['Nespresso', 'Bottled',]))
    farms = FarmPhotos.objects.all()

    context = {
        'is_worldwide': is_worldwide,
        'coffee_list': coffee_list.filter(special=False),
        'special_coffee_list': coffee_list.filter(special=True),
        'taster_coffee_list': CoffeeType.objects.tasters().order_by('-id'),
        'coffee_rating': CoffeeType.objects.avg_rating(),
        'brew_methods': brew_methods,
        'brew_methods_oneoff': brew_methods_oneoff,
        'key': settings.PUBLISHABLE_KEY,
        'out_of_credits': out_of_credits,
        'stripe_key': settings.PUBLISHABLE_KEY,
        'preferences_form': PreferencesForm(),
        'current_brew': BrewMethod.objects.get(name_en='None'),
        'current_package': 'WB',
        'current_domain': Site.objects.get_current().domain,
        'farms': farms,
    }

    return render(request, 'coffees/index.html', context)


@geo_check
def pods(request, is_worldwide):
    try:
        customer = request.user.customer
        out_of_credits = customer.amount == 0 and not customer.stripe_id
    except:
        out_of_credits = False

    coffee_list = CoffeeType.objects.nespresso(only_active=False).order_by('-id')

    context = {
        'is_worldwide': is_worldwide,
        'coffee_list': coffee_list.filter(special=False),
        'special_coffee_list': coffee_list.filter(mode=True, special=True),
        'key': settings.PUBLISHABLE_KEY,
        'out_of_credits': out_of_credits,
        'stripe_key': getattr(settings, 'PUBLISHABLE_KEY'),
        'stripe_key': settings.PUBLISHABLE_KEY,
        'current_domain': Site.objects.get_current().domain
    }

    return render(request, 'coffees/nespresso.html', context)


@json_view
@geo_check
def get_shipping_rates(request, is_worldwide, cid=None, coffee_ids=None, gear_id=None, qty=None, overall_weight=0):
    if not overall_weight:
        # gear order
        if gear_id:
            gear = CoffeeGear.objects.get(id=gear_id)
            overall_weight = gear.weight * qty
        # coffee order
        else:
            if not coffee_ids:
                json_data = json.loads(request.POST.get('my_data'))
                coffee_ids = json_data.get('coffee_ids')
                cid = json_data.get('cid')

                request.session['cart_quantity'] = json_data.get('qty')
                request.session['country_code'] = json_data.get('cid')

            overall_weight = 0
            try:
                for i in coffee_ids:
                    coffee = CoffeeType.objects.get(id=i['id'])
                    overall_weight += coffee.weight * int(i['qty'])
            except TypeError:
                # coffee_ids contains one item only
                coffee = CoffeeType.objects.get(id=coffee_ids.get('id'))
                overall_weight = coffee.weight * int(coffee_ids['qty'])

    try:
        cname = dict(countries)[cid]
        if cname in zone1:
            shipping_cost = round(overall_weight // 100 * 1.1 + (1 if (overall_weight % 100) else 0) * 1.1, 2)
            zone = 1
        elif cname in zone2:
            shipping_cost = round(0.7 + (overall_weight - 20) / 10 * 0.25, 2)
            zone = 2
        else:
            shipping_cost = round(1.3 + (overall_weight - 20) / 10 * 0.35, 2)
            zone = 3
    except Exception as e:
        cname = None
        shipping_cost = 0
        zone = 3

    # singapore
    if not is_worldwide or (cid == 'SG'):
        shipping_cost = 0

    request.session['shipping_cost'] = shipping_cost
    request.session['country_name'] = cname

    return {
        'success': True,
        'overall_weight': overall_weight,
        'cname': cname,
        'zone': zone,
        'shipping_cost': shipping_cost,
    }


def charge_client(request, stripe_customer_id, amount):
    context = {}
    amount = int(Decimal(amount).quantize(Decimal('.001'), rounding=ROUND_UP) * 100)
    try:
        charge = stripe.Charge.create(
            amount=amount,
            currency='SGD',
            customer=stripe_customer_id,
            description='Cart order',
            metadata={})
        context['success'] = charge.get('status')
        context['amount'] = charge.get('amount')
        context['id'] = charge.get('id')
        request.session['stripe_amount'] = charge.get('amount')
    except stripe.error.CardError, e:
        body = e.json_body
        err = body['error']
        context['error'] = err['message']
    except stripe.error.RateLimitError, e:
        context['error'] = 'Too many requests made to the API too quickly.'
    except stripe.error.InvalidRequestError, e:
        context['error'] = "Invalid parameters were supplied to Stripe's API."
        context['message'] = e
    except stripe.error.AuthenticationError, e:
        context['error'] = "Authentication with Stripe's API failed."
    except stripe.error.APIConnectionError, e:
        context['error'] = "Network communication with Stripe failed."
    except stripe.error.StripeError, e:
        context['error'] = "Display a very generic error to the user,\
            and maybe send yourself an email."
    except Exception as e:
        context['error'] = 'Critical Stripe error.', e

    return context


def detail(request, coffee_id):
    if request.method == 'POST':
        print 'detail, POST =', request.POST.items()
        coffee_id = request.POST.get('coffee-id')

        try:
            coffee = CoffeeType.objects.get(id=coffee_id)
            customer = request.user.customer
            preferences = customer.preferences
        except:
            coffee = customer = preferences = None

        if 'one-off' in request.POST:
            if coffee:

                if not request.POST.get('isNespresso'):
                    selected_brew = BrewMethod.objects.get(id=request.POST.get('brew-method'))
                    selected_package = request.POST.get('package-method', )
                else:
                    selected_brew = BrewMethod.objects.get(name_en='Nespresso')
                    selected_package = Preferences.DRIP_BAGS

                order = Order.objects.create(
                    customer=customer,
                    coffee=coffee,
                    date=timezone.now(),
                    shipping_date=get_shipping_date(),
                    amount=coffee.amount_one_off,
                    interval=0,
                    recurrent=False,
                    status=Order.ACTIVE,
                    brew=selected_brew,
                    package=selected_package,
                )

                mailing_list.update_mailchimp_tracking(request, order, MailchimpCampaignStats.PURCHASED)

                request.session['active_tab'] = 'active_one_offs'

                new_purchase_amount = float(order.amount)
                request.session['new_purchase_amount'] = new_purchase_amount

                add_event.delay(
                    customer_id=order.customer.id,
                    event='created-one-off',
                    order_id=order.id)

        if 'subscription' in request.POST:
            if preferences and coffee:
                if request.POST.get('isNespresso') == 'False':
                    request.session['active_tab'] = 'active_subscriptions'
                    brew = preferences.brew or BrewMethod.objects.get(name_en='Espresso')
                else:
                    request.session['active_tab'] = 'active_subscriptions_pods'
                    brew = BrewMethod.objects.get(name_en='Nespresso')

                order = Order.objects.create(
                    customer=customer,
                    coffee=coffee,
                    date=timezone.now(),
                    shipping_date=get_shipping_date(),
                    amount=coffee.amount,
                    interval=get_interval(preferences.interval),
                    recurrent=True,
                    status=Order.ACTIVE,
                    brew=brew,
                    package=preferences.package,
                    different=preferences.different,
                )

                mailing_list.update_mailchimp_tracking(request, order, MailchimpCampaignStats.PURCHASED)

                add_event.delay(
                    customer_id=order.customer.id,
                    event='created-subscription',
                    order_id=order.id)

                Reminder.objects.filter(email=customer.user.email, resumed=None).update(completed=True)

        return redirect('profile')

    else:
        customer = Customer.objects.get(user=request.user)
        preferences = customer.preferences

        subscribe = True
        if request.GET.get('subscribe'):
            if request.GET['subscribe'] == '0':
                subscribe = False

        isNespresso = True
        if request.GET.get('isNespresso'):
            if request.GET['isNespresso'] == '0':
                isNespresso = False

        context = {
            'key': settings.PUBLISHABLE_KEY,
            'coffee': CoffeeType.objects.get(id=coffee_id),
            'subscribe': subscribe,
            'isNespresso': isNespresso,
        }

        context['brew_methods'] = BrewMethod.objects.sorted(~Q(name_en='Nespresso'))
        context['preferences_form'] = PreferencesForm()

        # Need to clean up
        context['current_brew'] = preferences.brew or BrewMethod.objects.get(name_en="None")
        context['current_package'] = preferences.package

        return render(request, 'coffees/detail.html', context)


@geo_check
def gifts(request, is_worldwide):
    context = {}

    try:
        gift = CoffeeType.objects.filter(name__in=['Gift for him', 'Gift for her'])
        print gift
    except:
        gift = None

    if request.method == 'POST':
        print '* POST Gift'

        try:
            customer = Customer.objects.get(user=request.user)
            coffee = CoffeeType.objects.get(name=request.POST.get('gift'))
            preferences = Preferences.objects.get(customer=customer)
        except:
            customer = preferences = None

        if preferences:
            order = Order(
                customer=customer,
                coffee=coffee,
                date=timezone.now(),
                shipping_date=datetime(2016, 2, 1, 0, 0, 0, 0, pytz.timezone('Asia/Singapore')),
                amount=coffee.amount,
                interval=0,
                recurrent=False,
                status=Order.ACTIVE,
                brew=preferences.brew,
                package=preferences.package,
            )
            order.save()
            print 'Gift ordered', order

        request.session['active_tab'] = 'active_one_offs'

        return redirect('profile')

    context['coffee'] = gift
    context['is_worldwide'] = is_worldwide

    return render(request, 'coffees/gifts.html', context)


@geo_check
def send_friend(request, is_worldwide):
    context = {}
    context['stripe_key'] = settings.PUBLISHABLE_KEY
    context['is_worldwide'] = is_worldwide
    context['current_domain'] = Site.objects.get_current().domain

    return render(request, 'coffees/send-friend.html', context)


class CoffeeGearListView(ListView):
    queryset = (CoffeeGear.objects.filter(special='')
                                  .prefetch_related('images'))
    context_object_name = 'gears'
    template_name = 'coffees/shop-gift.html'


class CoffeeGearSetListView(ListView):
    queryset = (CoffeeGear.objects.filter(special='set', available=True)
                                  .prefetch_related('images'))
    context_object_name = 'gears'
    template_name = 'coffees/shop-gift-set.html'

    def get_context_data(self, **kwargs):
        context = super(CoffeeGearSetListView, self).get_context_data(**kwargs)
        context['brew_methods'] = BrewMethod.objects.sorted(
            ~Q(name_en='None'), ~Q(name_en='Nespresso'))
        return context


@require_POST
def gift_sets_voucher(request):
    result = {}
    result['found'] = False
    voucher_name = request.POST.get('voucher-name', '')

    fch = forms.CharField()
    try:
        voucher_name = fch.clean(voucher_name).strip().upper()
    except forms.ValidationError:
        return JsonResponse(result)

    try:
        voucher = (
            Voucher.objects.filter(mode=True, category__name='GiftSets')
                           .get(name=voucher_name))
    except Voucher.DoesNotExist:
        return JsonResponse(result)
    else:
        result['found'] = True
        request.session['voucher-name'] = voucher.name

    if voucher.discount2:
        result['discount'] = '$%d' % voucher.discount2
    else:
        result['discount'] = '%s%%' % voucher.discount
    return JsonResponse(result)


@require_POST
@geo_check
def buy_gear(request, is_worldwide):
    gear_id = request.POST.get('gear-id')
    address_id = request.POST.get('address-id')
    note = request.POST.get('note')
    chosen_date = request.POST.get('chosen_date')
    chosen_date = datetime.strptime(chosen_date, '%d/%m/%Y')

    gear_color_id = request.POST.get('gear-color-id', 0)
    quantity = request.POST.get('quantity', 1)
    packaging = request.POST.get('packaging', 0)
    brew_method_id = request.POST.get('brew-method-id', 0)
    voucher_name = (request.session.get('voucher-name') or
                    request.POST.get('voucher-name'))

    f = forms.IntegerField()
    fch = forms.CharField()

    gear_id = f.clean(gear_id)
    gear_color_id = f.clean(gear_color_id)
    quantity = f.clean(quantity)
    packaging = f.clean(packaging)
    brew_method_id = f.clean(brew_method_id)
    voucher = None
    if voucher_name:
        voucher_name = fch.clean(voucher_name)
        voucher_name = voucher_name.strip().upper()
        try:
            voucher = (
                Voucher.objects.filter(mode=True, category__name='GiftSets')
                               .get(name=voucher_name))
        except Voucher.DoesNotExist:
            pass
        else:
            request.session['gear_voucher'] = voucher.name

    details = {}
    if gear_color_id:
        color = CoffeeGearColor.objects.get(id=gear_color_id)
        details['Colour'] = color.name

    if quantity < 1:  # shit happens, right?
        quantity = 1
    details['Quantity'] = str(quantity)

    if packaging:
        packaging = 'Wholebeans' if packaging == 1 else 'Ground'
        request.session['gear_packaging'] = details['packaging'] = packaging

    if brew_method_id:
        brew_method = BrewMethod.objects.get(id=brew_method_id)
        request.session['gear_brew_method'] = details['brew_method'] = brew_method.name_en

    if not request.user.is_authenticated:
        return redirect(
            'preregister_gear',
            gear_id=gear_id,
            gear_qty=quantity,
            gear_color_id=gear_color_id,
        )

    customer = Customer.objects.get(user=request.user)
    gear = CoffeeGear.objects.get(id=gear_id)

    # now = timezone.now()
    # if (now.month == 1 and now.day < 9):
    #     details['Pre-Order'] = 'True'
    #     shipping_date = datetime(
    #         2017, 1, 9,
    #         hour=12, minute=0, second=0, microsecond=0,
    #         tzinfo=timezone.get_current_timezone())
    # else:
    #     shipping_date = get_shipping_date()

    price = gear.price * quantity
    if voucher:
        price -= price * voucher.discount / 100 + voucher.discount2
        # Mark voucher as used for current customer
        customer.vouchers.add(voucher)
        customer.save()
        voucher.count += 1
        voucher.save()

    # charge global users immediately
    # context = {}
    # if is_worldwide:
    #     get_shipping_rates(request, cid=customer.country.code, gear_id=gear.id, qty=quantity)
    #     shipping_cost = request.session.get('shipping_cost', 0)
    #     total_price = float(price) + shipping_cost
    #     context = charge_client(request, customer.stripe_id, total_price)

    context = charge_client(request, customer.stripe_id, price)
    if not context.get('error'):
        order = GearOrder.objects.create(
            customer=customer,
            gear=gear,
            shipping_date=chosen_date or get_shipping_date(),
            price=price,
            details=details,
            voucher=voucher,
        )

        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            pass
        else:
            order.address = address
            order.save()

        if note:
            order.details['gift_note'] = note
            order.save()

        request.session['new_purchase_amount'] = float(order.price)
    else:
        # TODO: show error to user
        pass

    request.session['active_tab'] = 'active_one_offs'

    return redirect('profile')


@require_POST
def set_stripe_credits(request):
    print '* Set Stripe'
    token = request.POST['stripeToken']
    customer = Customer.objects.get(user=request.user)
    if token:
        try:
            stripe_customer = stripe.Customer.create(
                source=token,
                email=customer.user.email,
                description='{} {}'.format(
                    customer.first_name,
                    customer.last_name
                    ),
                )
            stripe_data = stripe_customer.to_dict()
            request.session['last4'] = stripe_data['sources']['data'][0]['last4']
            request.session['exp_month'] = stripe_data['sources']['data'][0]['exp_month']
            request.session['exp_year'] = stripe_data['sources']['data'][0]['exp_year']
            customer.stripe_id = stripe_customer.id
            customer.card_details = '{}{}{}'.format(
                        request.session.get('last4'),
                        '{:0>2}'.format(
                            request.session.get('exp_month')),
                            request.session.get('exp_year')
                        )
            customer.save()

        except stripe.error.StripeError as e:
            body = e.json_body
            err  = body['error']

            print 'Stripe error when creating customer:'
            print 'Status is: %s' % e.http_status
            print 'Type is: %s' % err['type']
            print 'Code is: %s' % err['code']
            # param is '' in this case
            print 'Param is: %s' % err['param']
            print 'Message is: %s' % err['message']

            return {
                'success': False,
                'message': err['message']
            }
        except Exception as e:
            # Other errors unrelated to Stripe was thrown
            print 'Something else happened, completely unrelated to Stripe'
            print 'Error details:', e
            return {
                'success': False,
                'message': e.json_body['error']['message']
            }

    return redirect('coffees')


@require_POST
def shared_sticker(request):
    shared_post = request.POST.get('post')
    order_id = request.POST.get('order')
    hashtag = request.POST.get('hashtag')

    try:
        user_id, post_id = shared_post.split('_')
        user_id, post_id = int(user_id), int(post_id)
    except ValueError:
        return HttpResponse(status=500)

    try:
        hashtag = re.sub('[^#\w]', '', hashtag)
    except TypeError:
        hashtag = ''

    try:
        order_id = abs(int(order_id))
        order = Order.objects.get(pk=order_id)
        customer = order.customer_id
    except (ValueError, ObjectDoesNotExist):
        customer = None

    SharedCoffeeSticker.objects.create(
        customer_id=customer,
        user=user_id,
        post=post_id,
        hashtag=hashtag,
    )

    return HttpResponse(status=200)


@require_POST
@csrf_protect
@json_view
def cart_add(request):
    # isNespresso = request.POST.get('isNespresso') == u'True'
    coffee_id = int(request.POST.get('coffee-id'))
    brew_method = request.POST.get('brew-method')
    package_method = request.POST.get('package-method')
    quantity = request.POST.get('quantity')

    coffee = CoffeeType.objects.get(id=coffee_id)
    coffee_name = coffee.name

    try:
        if request.session.get('cart'):
            request.session['cart'].append({
                'coffee_id': coffee_id,
                'coffee_name': coffee_name,
                'quantity': quantity,
                'brew_method': brew_method,
                'package_method': package_method,
            })
        else:
            request.session['cart'] = [{
                'coffee_id': coffee_id,
                'coffee_name': coffee_name,
                'quantity': quantity,
                'brew_method': brew_method,
                'package_method': package_method,
            }]
    except Exception as e:
        print e

    request.session.modified = True

    for x in request.session.items():
        print x

    return {
                'success': True,
            }

@geo_check
def checkout(request, is_worldwide):
    try:
        customer = request.user.customer
    except:
        customer = None

    if request.GET.get("checkout") and not customer:
        # url = "{}?checkout=kokoshnik".format(reverse(login_user))
        url = "/accounts/login/?checkout=matryoshka"
        return HttpResponseRedirect(url)

    context = {}
    orders = []
    coffee_ids = []
    total = count = shipping_cost_bottled = 0

    cart_list = request.session.get('shopping-cart')

    if not cart_list:
        return redirect("profile")

    for cart_item in cart_list:
        quantity = int(cart_item.get('quantity', 0))
        if cart_item.get('coffee') and quantity > 0:
            try:
                coffee = CoffeeType.objects.get(id=cart_item.get('coffee').get('id'))
                brew = BrewMethod.objects.get(id=cart_item.get('coffee').get('brew_id'))
                package = PACKAGE_MAPPER[cart_item.get('coffee').get('package')]

                if coffee.is_bottled():
                    for i in range(quantity):
                        shipping_cost_bottled += 10 if shipping_cost_bottled == 0 else 5

                orders.append((coffee, brew, package, quantity))
                coffee_ids.append({
                    'id': coffee.id,
                    'qty': quantity,
                })

                total += coffee.amount_one_off * quantity
                count += quantity
            except Exception as e:
                logger.error(e)
        elif cart_item.get('gear') and quantity > 0:
            try:
                gear = CoffeeGear.objects.get(id=cart_item.get('gear').get('id'))

                orders.append((gear, quantity))
                coffee_ids.append({
                    'id': gear.id,
                    'qty': quantity,
                })

                total += gear.price * quantity
                count += quantity
            except Exception as e:
                logger.error(e)

    request.session['cart_quantity'] = count
    request.session['coffee_cost'] = round(total, 2)
    request.session['from_get_started'] = False
    request.session['from_shopping_cart'] = True
    request.session['from_preregister'] = False
    request.session['shipping_cost'] = shipping_cost_bottled

    request.session.pop('voucher', None)

    return redirect('register_worldwide')


# @require_POST
@geo_check
def cart_confirm(request, is_worldwide):
    '''
        Redirects either to registration if user has no account yet
        or to profile creating appropriate orders and charging client's card.
    '''
    request.session.pop('voucher', None)

    try:
        customer = Customer.objects.get(user=request.user)
    except:
        customer = None

    logger.debug('CONFIRM CART: {} [{}] Session: {}'.format(
        request.user, get_client_ip(request), request.session.items()))

    request.session['from_get_started'] = False
    request.session['from_shopping_cart'] = True

    if customer:
        return redirect('cart_process')
    elif request.session.get('shopping-cart'):
        return redirect('register_worldwide')
    else:
        return redirect('register')


@geo_check
def workshops(request, is_worldwide):
    """
    This function will returns the list of workshops
    """
    try:
        customer = Customer.objects.get(user=request.user)
        # User who has been registered without credit card but with credits by a friend
        # goes out of credits and should provide credit card details
        out_of_credits = customer.amount == 0 and not customer.stripe_id
    except:
        out_of_credits = False

    workshops_list = WorkShops.objects.filter(status=True)
    farms = FarmPhotos.objects.all()

    context = {
        'is_worldwide': is_worldwide,
        'workshops_list': workshops_list,
        'key': settings.PUBLISHABLE_KEY,
        'out_of_credits': out_of_credits,
        'stripe_key': settings.PUBLISHABLE_KEY,
        'current_domain': Site.objects.get_current().domain,
        'farms': farms,
        'workshop': True
    }
    return render(request, 'coffees/index.html', context)
