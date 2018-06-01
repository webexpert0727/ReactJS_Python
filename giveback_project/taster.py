# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import logging
from datetime import timedelta

from jsonview.decorators import json_view

import stripe

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.sites.models import Site
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from coffees.models import BrewMethod, CoffeeType

from customauth.models import MyUser

from customers.forms import GS_CustomerForm, GS_PreferencesForm
from customers.models import Customer, Order, Preferences, Voucher
from customers.tasks import add_event, mailchimp_subscribe, send_email_async

from get_started.forms import CustomRegistrationForm

from giveback_project.helpers import get_shipping_date

from reminders.models import Reminder


logger = logging.getLogger('giveback_project.' + __name__)
stripe.api_key = settings.SECRET_KEY


@json_view
def trial(request, which=None):
    print 'trial, type: ', which
    result = context = {}

    if which == 'shotpods':
        taster_pack = CoffeeType.objects.get(name='Shotpods Taster Pack')
    else:
        taster_pack = CoffeeType.objects.get(name='Taster pack')
    print '* Got taster pack', taster_pack

    if request.method == "POST":
        print request.POST

        if 'one-password1' in request.POST:
            rf = CustomRegistrationForm(request.POST, prefix='one')
            if rf.is_valid():
                print 'Registration form valid'
                result['success'] = True

                request.session['email'] = rf.cleaned_data['email']
                request.session['password'] = request.POST['one-password1']

                mailchimp_subscribe.delay(email=request.session.get('email'))
            else:
                errors = rf.errors
                print 'Registration form invalid!', errors
                return HttpResponse(json.dumps(errors))

        if 'two-first_name' in request.POST:
            cf = GS_CustomerForm(request.POST, prefix='two')
            pf = GS_PreferencesForm(request.POST, prefix='tri')

            if cf.is_valid():
                print 'Customer form valid'

                result['success'] = True

                request.session['first_name'] = request.POST['two-first_name']
                request.session['last_name'] = request.POST['two-last_name']
                request.session['line1'] = request.POST['two-line1']
                request.session['line2'] = request.POST['two-line2']
                request.session['postcode'] = request.POST['two-postcode']

                mailchimp_subscribe.delay(
                    email=request.session.get('email'),
                    merge_vars={
                        'FNAME': request.session.get('first_name'),
                        'LNAME': request.session.get('last_name'),
                    },
                )

            else:
                errors = cf.errors
                print 'Customer form invalid!', errors
                return HttpResponse(json.dumps(errors))

        if 'stripeToken' in request.POST:
            print '* Submit'

            try:
                user = MyUser(email=request.session['email'])
                user.set_password(request.session['password'])
                user.save()
                print '* New user', user
            except Exception as e:
                print e

            try:
                customer = Customer(
                    user=user,
                    first_name=request.session['first_name'],
                    last_name=request.session['last_name'],
                    line1=request.session['line1'],
                    line2=request.session['line2'],
                    postcode=request.session['postcode'],
                    stripe_id=request.session['stripe_id']
                )
                customer.save()
                add_event.delay(
                    customer_id=customer.id,
                    event='signed-up',
                    data={'trial': True})
                print '* New customer', customer
            except Exception as e:
                print e

            try:
                if which == 'shotpods':
                    random_coffee = CoffeeType.objects.nespresso().filter(
                        special=False).first()
                    random_brew = BrewMethod.objects.get(name_en='Nespresso')
                else:
                    random_coffee = CoffeeType.objects.bags().filter(
                        special=False).first()
                    random_brew = BrewMethod.objects.get(name_en='None')
                preferences = Preferences(
                    customer=customer,
                    coffee=random_coffee,
                    brew=random_brew,
                    package=Preferences.DRIP_BAGS
                )
                preferences.save()
                print '* New preferences', preferences
            except Exception as e:
                print e

            try:
                trial_voucher = Voucher.objects.get(name='Taster Pack')
                trial_voucher.count += 1
                trial_voucher.save()
            except:
                trial_voucher = Voucher(
                    name='Taster Pack',
                    discount=0,
                    count=1
                )
                trial_voucher.save()

            try:
                order = Order.objects.create(
                    customer=customer,
                    coffee=taster_pack,
                    date=timezone.now(),
                    shipping_date=get_shipping_date(),
                    amount=taster_pack.amount,
                    status=Order.ACTIVE,
                    brew=preferences.brew,
                    package=Preferences.DRIP_BAGS,
                    interval=0,
                    voucher=trial_voucher
                )
                print '* Subscription created'

                add_event.delay(
                    customer_id=customer.id,
                    event='created-trial',
                    order_id=order.id)

            except Exception as e:
                print e

            new_user = authenticate(
                email=user.email,
                password=request.session['password'])
            login(request, new_user)

            context = {
                'coffee': taster_pack.name,
                'image': taster_pack.img.url,
            }

            ctz = timezone.get_current_timezone()
            now = ctz.normalize(timezone.now())

            # If there are other reminders (for example from Gets Started)
            # mark they as completed
            Reminder.objects.filter(email=user.email, resumed=None).update(completed=True)
            # Send email in a week if taster pack
            Reminder.objects.create(
                username=customer.first_name,
                email=customer.user.email,
                from_email='Hook Coffee <hola@hookcoffee.com.sg>',
                subject='Which was your favourite?',
                template_name='Which was your favourite?',
                scheduled=now + timedelta(days=7),
            )
            # Send notification
            send_email_async.delay(
                subject='Welcome on board!',
                template='O1 - First order on a subscription (done)',
                to_email=customer.get_email(),
                from_email='Ernest from Hook Coffee <hola@hookcoffee.com.sg>',
                merge_vars={
                    'USERNAME': customer.first_name,
                    'DOMAIN_NAME': request.META.get('HTTP_HOST'),
                }
            )
            return render(request, 'get_started/thankyou-trial.html', context)

        return result

    else:
        rf = CustomRegistrationForm(prefix='one')
        cf = GS_CustomerForm(prefix='two')
        pf = GS_PreferencesForm(prefix='tri')

        context['reg_form'] = rf
        context['cus_form'] = cf
        context['pre_form'] = pf
        context['stripe_key'] = settings.PUBLISHABLE_KEY
        context['taster_pack'] = taster_pack
        context['current_domain'] = Site.objects.get_current().domain

    return render(request, 'trial.html', context)


@json_view
def set_stripe_trial(request):
    token = request.POST['stripeToken']
    if token:
        try:
            stripe_customer = stripe.Customer.create(
                source=token,
                email=request.session['email'],
                description='{} {}'.format(
                    request.session['first_name'],
                    request.session['last_name'],
                ),
            )
            request.session['stripe_id'] = stripe_customer.id
            print '* Stripe set', request.session['stripe_id']
            return {
                'success': True,
                'stripe_id': request.session['stripe_id']
            }
        except stripe.error.StripeError as e:
            # Errors to catch:
            #
            # Card is declined.
            # Too many requests made to the API too quickly.
            # Invalid parameters were supplied to Stripe's API.
            # Authentication with Stripe's API failed.
            # Network communication with Stripe failed
            #
            # more info at https://stripe.com/docs/api/python#errors
            body = e.json_body
            err = body['error']

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

    return {
        'success': False,
    }


@json_view
def taster3x80g(request):
    result = context = {}

    if request.method == "POST":

        if 'one-password1' in request.POST:
            rf = CustomRegistrationForm(request.POST, prefix='one')

            if rf.is_valid():
                result['success'] = True
                try:
                    details = json.loads(request.POST.get('array'))

                    request.session['email'] = rf.cleaned_data['email']
                    request.session['password'] = request.POST['one-password1']
                    request.session['brew'] = details['brew']
                    request.session['package'] = details['package']

                    mailchimp_subscribe.delay(email=request.session.get('email'))
                except Exception as e:
                    print e
            else:
                errors = rf.errors
                return HttpResponse(json.dumps(errors))

        if 'two-first_name' in request.POST:
            cf = GS_CustomerForm(request.POST, prefix='two')
            pf = GS_PreferencesForm(request.POST, prefix='tri')

            if cf.is_valid():
                result['success'] = True

                request.session['first_name'] = request.POST['two-first_name']
                request.session['last_name'] = request.POST['two-last_name']
                request.session['line1'] = request.POST['two-line1']
                request.session['line2'] = request.POST['two-line2']
                request.session['postcode'] = request.POST['two-postcode']

                mailchimp_subscribe.delay(
                    email=request.session.get('email'),
                    merge_vars={
                        'FNAME': request.session.get('first_name'),
                        'LNAME': request.session.get('last_name'),
                    },
                )

            else:
                errors = cf.errors
                return HttpResponse(json.dumps(errors))

        if 'stripeToken' in request.POST:
            try:
                user = MyUser(email=request.session['email'])
                user.set_password(request.session['password'])
                user.save()
            except Exception as e:
                print e

            try:
                customer = Customer(
                    user=user,
                    first_name=request.session['first_name'],
                    last_name=request.session['last_name'],
                    line1=request.session['line1'],
                    line2=request.session['line2'],
                    postcode=request.session['postcode'],
                    stripe_id=request.session['stripe_id']
                    )
                customer.save()
                add_event.delay(
                    customer_id=customer.id,
                    event='signed-up',
                    data={'taster3x80g': True})

            except Exception as e:
                print e

            random_coffee = CoffeeType.objects.bags().filter(
                special=False).first()
            preferences = Preferences(
                customer=customer,
                coffee=random_coffee,
                brew=BrewMethod.objects.get(id=request.session.get('brew')),
                package=request.session['package']
                )
            preferences.save()

            taster3x80g = CoffeeType.objects.get(name='Taster 3x80g')

            try:
                voucher = Voucher.objects.get(name='Taster 3x80g')
                voucher.count += 1
                voucher.save()
            except:
                voucher = Voucher(
                    name='Taster 3x80g',
                    discount=0,
                    count=1
                    )
                voucher.save()

            try:
                order = Order.objects.create(
                    customer=customer,
                    coffee=taster3x80g,
                    date=timezone.now(),
                    shipping_date=get_shipping_date(),
                    amount=taster3x80g.amount,
                    status=Order.ACTIVE,
                    brew=preferences.brew,
                    package=preferences.package,
                    interval=0,
                    voucher=voucher
                )
                add_event.delay(
                    customer_id=customer.id,
                    event='created-taster3x80g',
                    order_id=order.id)
            except Exception as e:
                print e

            new_user = authenticate(email=user.email,
                password=request.session['password'])
            login(request, new_user)

            context = {
                'coffee': taster3x80g.name,
                'image': taster3x80g.img.url,
            }

            # Send reminding email in a week
            ctz = timezone.get_current_timezone()
            now = ctz.normalize(timezone.now())

            # If there are other reminders (for example from Gets Started)
            # mark they as completed
            Reminder.objects.filter(email=user.email).update(completed=True)
            # Send email in a week if taster pack
            Reminder.objects.create(
                username=customer.first_name,
                email=customer.user.email,
                from_email='Hook Coffee <hola@hookcoffee.com.sg>',
                subject='Which was your favourite?',
                template_name='Which was your favourite?',
                scheduled=now + timedelta(days=7),
            )

            # Send summary email
            send_email_async.delay(
                subject='Welcome on board!',
                template='O1 - First order on a subscription (done)',
                to_email=customer.get_email(),
                from_email='Ernest from Hook Coffee <hola@hookcoffee.com.sg>',
                merge_vars={
                    'USERNAME': customer.first_name,
                    'DOMAIN_NAME': request.META.get('HTTP_HOST'),
                }
            )
            return render(request, 'get_started/thankyou-trial.html', context)

        return result

    else:
        rf = CustomRegistrationForm(prefix='one')
        cf = GS_CustomerForm(prefix='two')
        pf = GS_PreferencesForm(prefix='tri')
        context['reg_form'] = rf
        context['cus_form'] = cf
        context['pre_form'] = pf
        context['stripe_key'] = settings.PUBLISHABLE_KEY
        context['default_pack'] = Preferences.WHOLEBEANS
        context['brew_methods'] = BrewMethod.objects.sorted(~Q(name_en='Nespresso'))

    return render(request, 'taster/taster3x80g.html', context)


@json_view
def taster5x(request):
    result = context = {}

    if request.method == "POST":

        if 'one-password1' in request.POST:
            rf = CustomRegistrationForm(request.POST, prefix='one')

            if rf.is_valid():
                result['success'] = True

                request.session['email'] = rf.cleaned_data['email']
                request.session['password'] = request.POST['one-password1']

                mailchimp_subscribe.delay(email=request.session.get('email'))
            else:
                errors = rf.errors
                return HttpResponse(json.dumps(errors))

        if 'two-first_name' in request.POST:
            cf = GS_CustomerForm(request.POST, prefix='two')
            pf = GS_PreferencesForm(request.POST, prefix='tri')

            if cf.is_valid():
                result['success'] = True

                request.session['first_name'] = request.POST['two-first_name']
                request.session['last_name'] = request.POST['two-last_name']
                request.session['line1'] = request.POST['two-line1']
                request.session['line2'] = request.POST['two-line2']
                request.session['postcode'] = request.POST['two-postcode']

                mailchimp_subscribe.delay(
                    email=request.session.get('email'),
                    merge_vars={
                        'FNAME': request.session.get('first_name'),
                        'LNAME': request.session.get('last_name'),
                    },
                )

            else:
                errors = cf.errors
                return HttpResponse(json.dumps(errors))

        if 'stripeToken' in request.POST:
            try:
                user = MyUser(email=request.session['email'])
                user.set_password(request.session['password'])
                user.save()
            except Exception as e:
                print e

            try:
                customer = Customer(
                    user=user,
                    first_name=request.session['first_name'],
                    last_name=request.session['last_name'],
                    line1=request.session['line1'],
                    line2=request.session['line2'],
                    postcode=request.session['postcode'],
                    stripe_id=request.session['stripe_id']
                    )
                customer.save()
                add_event.delay(
                    customer_id=customer.id,
                    event='signed-up',
                    data={'taster5x': True})

            except Exception as e:
                print e

            random_coffee = CoffeeType.objects.bags().filter(
                special=False).first()
            preferences = Preferences(
                customer=customer,
                coffee=random_coffee,
                brew=BrewMethod.objects.get(name_en='None'),
                package=Preferences.DRIP_BAGS
                )
            preferences.save()

            taster5x = CoffeeType.objects.get(name='Taster 5x')

            try:
                voucher = Voucher.objects.get(name='Taster 5x')
                voucher.count += 1
                voucher.save()
            except:
                voucher = Voucher(
                    name='Taster 5x',
                    discount=0,
                    count=1
                    )
                voucher.save()

            try:
                order = Order.objects.create(
                    customer=customer,
                    coffee=taster5x,
                    date=timezone.now(),
                    shipping_date=get_shipping_date(),
                    amount=taster5x.amount,
                    status=Order.ACTIVE,
                    brew=preferences.brew,
                    package=preferences.package,
                    interval=0,
                    voucher=voucher
                )
                add_event.delay(
                    customer_id=customer.id,
                    event='created-taster5x',
                    order_id=order.id)
            except Exception as e:
                print e

            new_user = authenticate(email=user.email,
                password=request.session['password'])
            login(request, new_user)

            context = {
                'coffee': taster5x.name,
                'image': taster5x.img.url,
            }

            # Send reminding email in a week
            ctz = timezone.get_current_timezone()
            now = ctz.normalize(timezone.now())

            # If there are other reminders (for example from Gets Started)
            # mark they as completed
            Reminder.objects.filter(email=user.email).update(completed=True)
            # Send email in a week if taster pack
            Reminder.objects.create(
                username=customer.first_name,
                email=customer.user.email,
                from_email='Hook Coffee <hola@hookcoffee.com.sg>',
                subject='Which was your favourite?',
                template_name='Which was your favourite?',
                scheduled=now + timedelta(days=7),
            )

            # Send summary email
            send_email_async.delay(
                subject='Welcome on board!',
                template='O1 - First order on a subscription (done)',
                to_email=customer.get_email(),
                from_email='Ernest from Hook Coffee <hola@hookcoffee.com.sg>',
                merge_vars={
                    'USERNAME': customer.first_name,
                    'DOMAIN_NAME': request.META.get('HTTP_HOST'),
                }
            )
            return render(request, 'get_started/thankyou-trial.html', context)

        return result

    else:
        rf = CustomRegistrationForm(prefix='one')
        cf = GS_CustomerForm(prefix='two')
        pf = GS_PreferencesForm(prefix='tri')

        context['reg_form'] = rf
        context['cus_form'] = cf
        context['pre_form'] = pf
        context['stripe_key'] = settings.PUBLISHABLE_KEY

    return render(request, 'taster/taster5x.html', context)
