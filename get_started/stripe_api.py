# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
from decimal import ROUND_UP, Decimal

import stripe
from django.conf import settings
from jsonview.decorators import json_view
from unidecode import unidecode

from customers.models import CardFingerprint

logger = logging.getLogger('giveback_project.' + __name__)
stripe.api_key = settings.SECRET_KEY


@json_view
def register(request):
    token = request.POST.get('stripeToken')
    if token:
        try:
            first_name = unidecode(request.session.get('first_name'))
            last_name = unidecode(request.session.get('last_name'))
            stripe_customer = stripe.Customer.create(
                source=token,
                email=request.session.get('email'),
                description='{} {}'.format(first_name, last_name))
            request.session['stripe_id'] = stripe_customer.id
            stripe_data = stripe_customer.to_dict()
            request.session['last4'] = stripe_data['sources']['data'][0]['last4']
            request.session['exp_month'] = stripe_data['sources']['data'][0]['exp_month']
            request.session['exp_year'] = stripe_data['sources']['data'][0]['exp_year']

            card = stripe_data['sources']['data'][0]
            fingerprint = card['fingerprint']

            already_registered = CardFingerprint.objects.filter(
                fingerprint=fingerprint)

            error_msg = ('Oops! seems like you have an account all set up. '
                         'If you do not have an account, please contact us.')

            if already_registered.exists() and stripe_customer['livemode']:
                logger.warning(
                    'Attempt to register with an already used credit card.',
                    extra={
                        'data': {
                            'card_fingerprint': fingerprint,
                            'email': request.session.get('email'),
                            'customers_with_same_card': list(
                                already_registered.distinct('customer').values_list(
                                    'customer__id', 'customer__user__email')),
                        },
                        'stack': True,
                    }
                )
                return {'success': False, 'message': error_msg}

            return {
                'success': True,
                'stripe_id': stripe_customer.id
            }
        except stripe.error.StripeError as e:
            body = e.json_body
            err  = body['error']
            logger.error(
                'Stripe error when creating customer: %s',
                request.session.get('email'),
                extra={'data': body.get('error', {})},
                exc_info=True)
            return {
                'success': False,
                'message': err['message']
            }
        except Exception as e:
            logger.error(
                'Stripe error when creating customer [Else]: %s',
                request.session.get('email'),
                exc_info=True)
            return {
                'success': False,
                'message': e.json_body['error']['message']
            }
    return {
        'success': False
    }


def charge(request, stripe_customer_id, amount, metadata=None):
    context = {}
    amount = int(Decimal(amount).quantize(Decimal('.001'), rounding=ROUND_UP) * 100)
    try:
        charge = stripe.Charge.create(
            amount=amount,
            currency='SGD',
            customer=stripe_customer_id,
            description='Cart order',
            metadata=metadata)
        context['status'] = charge.get('status')
        context['paid'] = charge.get('paid')
        context['amount'] = charge.get('amount')
        context['charge_id'] = charge.get('id')
        request.session['stripe_amount'] = charge.get('amount')
    except stripe.error.CardError, e:
        body = e.json_body
        err = body['error']
        context['error'] = err['message']
        context['code'] = err['code']
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
        logger.error(
            'Critical Stripe error: %s', request.session.get('email'),
            exc_info=True)
        context['error'] = 'Critical Stripe error.', e

    return context
