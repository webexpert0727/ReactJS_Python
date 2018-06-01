# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json
import logging
import os
import time
import urllib2
from datetime import datetime, timedelta

from celery.schedules import crontab
from celery.task import Task, periodic_task

from intercom import Event as IntercomEvent
from intercom import Intercom
from intercom import ResourceNotFound
from intercom import Tag as IntercomTag
from intercom import User as IntercomUser

import mailchimp

import stripe

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone
from django.utils.dateformat import format as dt_format

from get_started.models import GetStartedResponse

from giveback_project import celery_app

from manager.models import IntercomLocal

from reminders.models import Reminder

from loyale.mixin import POINTS_FOR_EXP_SURVEY, PointMixin

from .models import CardFingerprint, Customer, Order, ShoppingCart


stripe.api_key = settings.SECRET_KEY

Intercom.app_id = settings.INTERCOM_APP_ID
Intercom.app_api_key = settings.INTERCOM_API_KEY
DEFAULT_FROM_EMAIL = settings.DEFAULT_FROM_EMAIL

SC_WAITING_TIME_1 = 4
SC_WAITING_TIME_2 = 24
SC_WAITING_TIME_3 = 48

CTZ = timezone.get_current_timezone()
point_mixin = PointMixin()

logger = logging.getLogger('giveback_project.' + __name__)


@celery_app.task(ignore_result=True)
def create_intercom_profile(email):
    user = IntercomUser.create(email=email)
    return user


@celery_app.task(ignore_result=True)
def update_intercom_profile(customer_id, data=None):
    customer = Customer.objects.select_related('user').get(id=customer_id)
    try:
        user = IntercomUser.find(email=customer.user.email)
    except ResourceNotFound:
        user = create_intercom_profile(email=customer.user.email)

    if data:
        # Partial update
        user.custom_attributes.update(data)
    else:
        # Full update
        user.name = customer.get_full_name()
        user.signed_up_at = customer.get_signed_up()
        user.custom_attributes.update({
            'last_login_at': customer.get_last_login(),
            'last_order_at': customer.get_last_order_date(),
            'paused': customer.subscription_is_paused(),
            'unsubscribed': customer.subscription_is_canceled(),
            'have_active_order': customer.has_active_order(),
            'address': customer.get_full_address(),
            'postcode': customer.postcode,
            'phone': customer.phone,
            'vouchers': customer.get_all_voucher_names(),
            'amount': round(customer.amount, 2),
            'total_spend': customer.get_total_spend(),
            'shipped_orders': customer.get_count_orders(),
            'facebook_id': customer.get_facebook_id(),
            'stripe_id': customer.stripe_id,
            'preferred_brew_method': customer.get_preferred_brew_method(),
            'has_bought_christmas_gift': customer.has_bought_christmas_gift(),
        })
    user.save()


@celery_app.task(ignore_result=True)
def add_event(customer_id, event, data=None, order_id=None):
    customer = Customer.objects.select_related('user').get(id=customer_id)

    if data is None:
        data = {}

    if order_id:
        data.update(_get_order_data(order_id=order_id))

    IntercomLocal.objects.create(
        customer=customer,
        event=event,
        data=data)

    try:
        IntercomUser.find(email=customer.user.email)
    except ResourceNotFound as e:
        create_intercom_profile(email=customer.user.email)
        logger.error('add_event [ResourceNotFound]: %s' % e)

    IntercomEvent.create(
        event_name=event,
        email=customer.user.email,
        created_at=int(time.time()),  # UTC
        metadata=data)


@celery_app.task(ignore_result=True)
def add_tag(customer_id, tag):
    customer = Customer.objects.select_related('user').get(id=customer_id)
    user = IntercomUser.find(email=customer.user.email)
    try:
        IntercomTag.tag_users(tag, [user.id])
    except ResourceNotFound as e:
        IntercomTag.create(name=tag)
        IntercomTag.tag_users(tag, [user.id])
        logger.error('add_tag [ResourceNotFound]: %s' % e)


@celery_app.task(ignore_result=True)
def sync_tags():
    customers = Customer.objects.select_related('user').all()
    for customer in customers:
        tags = customer.get_tags()
        if tags:
            user = IntercomUser.find(email=customer.user.email)
        for tag in tags:
            try:
                IntercomTag.tag_users(tag, [user.id])
            except ResourceNotFound as e:
                IntercomTag.create(tag)
                IntercomTag.tag_users(tag, [user.id])
                logger.error('sync_tags [ResourceNotFound]: %s' % e)


@celery_app.task(bind=True, ignore_result=True)
def sync_cancel_reason(self, customer_id, order_id=None):
    """
    Sync the cancellation reason of a subscription between TypeForm & Intercom
    """
    customer = Customer.objects.select_related('user').get(id=customer_id)
    try:
        responses = _get_typeform_responses(survey='RNSQTm')
    except Exception as e:
        logger.error('get typeform responses for %s', customer, exc_info=True)
        raise self.retry(exc=e, countdown=(25 * 60))  # retry in 25 minutes

    answers = {}
    for resp in responses:
        # find the customer's response
        if resp['hidden'].get('email') == customer.get_lower_email():
            answers = resp['answers']
            break
    else:
        logger.warning('sync_cancel_reason for %s:'
                       ' the answers not found.' % customer)
        raise self.retry(countdown=25 * 60)  # retry in 25 minutes

    cancel_reason = ' / '.join([answer for answer in answers.values()])
    # Add/Update customer attribte in intercom
    update_intercom_profile.delay(
        customer_id=customer.id,
        data={'cancellation-reason': cancel_reason or 'Other'})

    if order_id:
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            logger.error('Cancel reason. No order with id=%s found for %s',
                         order_id, customer, exc_info=True)
        else:
            order.details['cancellation-reason'] = cancel_reason
            order.save()

        # _create_cancellation_reminders(customer, order, answers.values())


@periodic_task(run_every=(crontab(minute='*/60')))
def check_answers_on_exp_survey():
    """
    Check TypeForm for find customers that pass exp survey by direct link.

    Mark them as answered on the survey and give beanie points.
    """
    try:
        responses = _get_typeform_responses(survey='HD2mS4')
    except Exception:
        logger.error('get typeform responses in check_answers', exc_info=True)
        raise

    user_emails = set(r['hidden'].get('email') for r in responses)
    user_emails = tuple(email.lower() for email in user_emails if email)
    if not user_emails:
        return
    customers = (Customer.objects
                 .select_related('user')
                 .extra(where=['lower(customauth_myuser.email) IN %s'],
                        params=[user_emails])
                 .filter(extra__isnull={'answered_exp_survey': True}))

    for customer in customers:
        try:
            with transaction.atomic():
                customer.extra['answered_exp_survey'] = True
                customer.save()

                # Fire intercom event
                add_event.delay(
                    customer_id=customer.id,
                    event='answered-the-exp-survey',
                    data={'by_direct_link': True})

                # Grant beanie points for completed exp survey
                point_mixin.grant_points(
                    user=customer.user, points=POINTS_FOR_EXP_SURVEY)
        except Exception:
            logger.error('check_answers_on_exp_survey', exc_info=True)


@celery_app.task(bind=True, ignore_result=True)
def give_points_for_exp_survey(self, customer_id):
    customer = Customer.objects.select_related('user').get(id=customer_id)
    try:
        responses = _get_typeform_responses(survey='HD2mS4')
    except Exception as e:
        logger.error('get typeform responses for %s', customer, exc_info=True)
        raise self.retry(exc=e, countdown=(25 * 60))  # retry in 25 minutes

    user_emails = set(r['hidden'].get('email') for r in responses)
    user_emails = tuple(email.lower() for email in user_emails if email)
    # find the customer's response
    user_answers_found = customer.get_lower_email() in user_emails

    if user_answers_found:
        # Grant beanie points for completed exp survey
        point_mixin.grant_points(
            user=customer.user, points=POINTS_FOR_EXP_SURVEY)
    else:
        logger.info('give_points_for_exp_survey for %s:'
                    ' the answers not found.' % customer)
        raise self.retry(countdown=25 * 60)  # retry in 25 minutes


@celery_app.task(bind=True, ignore_result=True)
def mailchimp_subscribe(self, email, is_lead=True, merge_vars=None, **kwargs):
    if not email:
        return
    if not merge_vars:
        merge_vars = {}

    email = email.lower()
    list_id = settings.MAILCHIMP_DEFAULT_LIST
    leads_segment_id = settings.MAILCHIMP_LEADS_SEGMENT
    try:
        m = mailchimp.Mailchimp(apikey=settings.MAILCHIMP_API_KEY)
        m.lists.subscribe(
            id=list_id,
            email={'email': email},
            double_optin=False,
            update_existing=True,
            send_welcome=False,
            merge_vars=merge_vars,
        )
    except mailchimp.Error as e:
        logger.error('Failed to subscribe %s', email, exc_info=True)
        raise self.retry(exc=e, countdown=5)
    else:
        if is_lead:
            mailchimp_segment_member_add.apply_async(
                (email, leads_segment_id), countdown=20)


@celery_app.task(bind=True, ignore_result=True)
def mailchimp_segment_member_add(self, email, seg_id):
    email = email.lower()
    list_id = settings.MAILCHIMP_DEFAULT_LIST
    try:
        m = mailchimp.Mailchimp(apikey=settings.MAILCHIMP_API_KEY)
        m.lists.static_segment_members_add(
            id=list_id,
            seg_id=seg_id,
            batch=[{'email': email}],
        )
    except mailchimp.Error as e:
        logger.error(
            'Failed to add %s to the leads segment', email, exc_info=True)
        raise self.retry(exc=e, countdown=5)


@celery_app.task(bind=True, ignore_result=True)
def mailchimp_segment_member_del(self, email, seg_id):
    email = email.lower()
    list_id = settings.MAILCHIMP_DEFAULT_LIST
    try:
        m = mailchimp.Mailchimp(apikey=settings.MAILCHIMP_API_KEY)
        m.lists.static_segment_members_del(
            id=list_id,
            seg_id=seg_id,
            batch=[{'email': email}],
        )
    except mailchimp.Error as e:
        logger.error(
            'Failed to delete %s from the leads segment', email, exc_info=True)
        raise self.retry(exc=e, countdown=5)


@celery_app.task(ignore_result=True)
def mailchimp_sync_customers_data():
    customers = Customer.objects.all().values('user__email', 'first_name', 'last_name')
    list_id = settings.MAILCHIMP_DEFAULT_LIST
    limit = 500
    for from_id in range(0, len(customers), limit):
        _customers = customers[from_id:from_id + limit]
        payload = [
            {'email': {
                'email': cus['user__email'].lower()
            },
             'merge_vars': {
                'FNAME': cus['first_name'],
                'LNAME': cus['last_name'],
            }} for cus in _customers]
        # need more merge vars? check methods:
        # - merge_var_add
        # - merge_var_update
        try:
            m = mailchimp.Mailchimp(apikey=settings.MAILCHIMP_API_KEY)
            m.lists.batch_subscribe(
                id=list_id,
                double_optin=False,
                update_existing=True,
                batch=payload,
            )
        except mailchimp.Error:
            logger.error('Failed to sync existing customers', exc_info=True)


@celery_app.task(ignore_result=True)
def mailchimp_sync_leads_data():
    customers = Customer.objects.all().values('user__email')
    cus_emails = [cus['user__email'].lower() for cus in customers]
    leads = (
        GetStartedResponse.objects.all()
        .exclude(email__in=cus_emails)
        .values('email', 'name'))

    list_id = settings.MAILCHIMP_DEFAULT_LIST
    limit = 500
    for from_id in range(0, len(leads), limit):
        _leads = leads[from_id:from_id + limit]
        payload = [
            {'email': {
                'email': lead['email'].lower()
            },
             'merge_vars': {
                'FNAME': lead['name'],
            }} for lead in _leads]
        # need more merge vars? check methods:
        # - merge_var_add
        # - merge_var_update
        try:
            m = mailchimp.Mailchimp(apikey=settings.MAILCHIMP_API_KEY)
            m.lists.batch_subscribe(
                id=list_id,
                double_optin=False,
                update_existing=True,
                batch=payload,
            )
        except mailchimp.Error:
            logger.error('Failed to sync leads', exc_info=True)


@celery_app.task(ignore_result=True)
def stripe_get_card_fingerprint(customer_id, cus_stripe_id):
    stripe_data = stripe.Customer.retrieve(cus_stripe_id)
    card = stripe_data['sources']['data'][0]
    fingerprint = card['fingerprint']
    CardFingerprint.objects.create(
        customer_id=customer_id,
        fingerprint=fingerprint,
    )


@celery_app.task(ignore_result=True)
def stripe_sync_customer_cards():
    limit = 100
    stripe_data = stripe.Customer.list(limit=limit, include=['total_count'])

    while len(stripe_data['data']) > 0:
        for cus in stripe_data:
            cards = cus['sources']['data']
            for card in cards:
                stripe_id = card['customer']
                fingerprint = card['fingerprint']
                try:
                    cus = Customer.objects.get(stripe_id=stripe_id)
                except Customer.DoesNotExist:
                    logger.error('Sync stripe data. Customer %s not found',
                                 stripe_id, exc_info=True)
                else:
                    CardFingerprint.objects.create(
                        customer=cus,
                        fingerprint=fingerprint,
                    )
        last_customer_id = stripe_data['data'][-1]['id']
        stripe_data = stripe.Customer.list(
            limit=limit,
            starting_after=last_customer_id)


def _get_order_data(order_id):
    order = Order.objects.select_related(
        'customer', 'coffee', 'brew', 'voucher').get(id=order_id)
    data = {
        'order': {
            'value': order.id,
            'url': 'https://hookcoffee.com.sg/admin/customers/order/%d/' % order.id,
        },
        'coffee': {
            'value': order.coffee.name,
            'url': 'https://hookcoffee.com.sg/admin/coffees/coffeetype/%d/' % order.coffee.id
        },
        'created_date': int(dt_format(order.date, 'U')),
        'shipping_date': int(dt_format(order.shipping_date, 'U')),
        'shipping_address': '[%s] %s %s %s' % (
            order.shipping_address['name'],
            order.shipping_address['line1'],
            order.shipping_address['line2'],
            order.shipping_address['postcode'],
        ),
        'price': {
            'currency': 'SGD',
            'amount': round(order.amount * 100, 2),
        },
        'details': str(order.details) if order.details else None,
        'voucher': order.voucher.name if order.voucher else None,
        'is-shotpods': True if order.brew.name == 'Nespresso' else False,
        'stripe_customer': order.customer.stripe_id or None,
    }
    return data


def _get_typeform_responses(survey, seconds=(120 * 60)):
    """Get responses submited on the surveys from TypeForm."""
    since = timezone.now() - timedelta(seconds=seconds)
    api_url = ('https://api.typeform.com/v1/form/%(survey)s?key=%(key)s'
               '&completed=true&since=%(since)d'
               '&order_by[]=date_submit,desc') % {
                   'key': settings.TYPEFORM_API_KEY,
                   'survey': survey,
                   'since': int(dt_format(since, 'U'))}
    resp = urllib2.urlopen(api_url)
    resp = json.loads(resp.read())
    return resp.get('responses', [])


# umputun-style constant defining
LIST_40305014_CHOICES = {
    "I DON'T DRINK ENOUGH FOR A COFFEE SUBSCRIPTION SERVICE": "much",
    "THE COFFEE WASN'T RIGHT FOR ME": "wrong",
    "IT IS TOO EXPENSIVE FOR ME": "expensive",
    "I DIDN'T QUITE ENJOY THE WHOLE EXPERIENCE": "upset",
    "I AM NOT DRINKING CAFFEINE": "caffeine",
    "OTHER": "other",
}

LIST_49961703_CHOICES = {
    "THE COFFEE WAS TOO LIGHT": "light",
    "THE COFFEE WAS TOO DARK": "dark",
    "THE COFFEE WAS SOUR": "sour",
    "OTHER": "other",
}

LIST_40409961_CHOICES = {
    "I RECEIVED THE WRONG ORDER": "wrong",
    "MY ORDER WENT MISSING/DAMAGED IN THE POST": "damaged",
    "I'M MOVING ABROAD": "abroad",
}

def _create_cancellation_reminders(customer, order, answers):
    answer = answers[-1].strip().upper()
    reason = LIST_40305014_CHOICES.get(answer)
    reason = LIST_49961703_CHOICES.get(answer, reason)
    reason = LIST_40409961_CHOICES.get(answer, reason)

    name = customer.first_name
    email = customer.user.email
    order_count = customer.get_count_orders()
    personal_voucher = Reminder.generate_voucher(name, email)

    ctz = timezone.get_current_timezone()
    now = ctz.normalize(timezone.now())

    if reason == "much":
        if order_count < 3:
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='Have you run out yet {}?'.format(name),
                template_name='React_Trial_TooMuchCoffeeEmail1',
                scheduled=now + timedelta(days=5),
            )
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='Tailor your coffee order with Hook...',
                template_name='React_Trial_TooMuchCoffeeEmail2',
                scheduled=now + timedelta(days=10),
            )
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='15 cups of coffee for just $14',
                template_name='React_Trial_TooMuchCoffeeEmail3',
                scheduled=now + timedelta(days=15),
            )
        else:
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='Have you run out yet {}?'.format(name),
                template_name='React_Active_TooMuchCoffeeEmail1',
                scheduled=now + timedelta(days=5),
            )
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='Tailor your coffee order with Hook...',
                template_name='React_Active_TooMuchCoffeeEmail2',
                scheduled=now + timedelta(days=10),
            )
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='15 cups of coffee for just $14',
                template_name='React_Active_TooMuchCoffeeEmail3',
                scheduled=now + timedelta(days=15),
            )

    elif reason == "light":
        recommended_coffee = order.customer.get_recommended_coffee_for_cancellations(order, reason)
        if order_count < 3:
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='{}, fancy $2 off each of your next three orders?'.format(name),
                template_name='React_Trial_CoffeeTooLight_Email1',
                scheduled=now + timedelta(days=7),
                recommended_coffee=recommended_coffee,
            )
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='Just 24 hours remaining to claim a $6 discount',
                template_name='React_Trial_CoffeeTooLight_Email2',
                scheduled=now + timedelta(days=14),
                recommended_coffee=recommended_coffee,
            )
        else:
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='{}, fancy $4 off each of your next three orders?'.format(name),
                template_name='React_Active_CoffeeTooLight_Email1',
                scheduled=now + timedelta(days=7),
                recommended_coffee=recommended_coffee,
            )
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='Just 24 hours remaining to claim a $12 discount',
                template_name='React_Active_CoffeeTooLight_Email2',
                scheduled=now + timedelta(days=14),
                recommended_coffee=recommended_coffee,
            )

    elif reason == "dark":
        recommended_coffee = order.customer.get_recommended_coffee_for_cancellations(order, reason)
        if order_count < 3:
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='{}, fancy $2 off each of your next three orders?'.format(name),
                template_name='React_Trial_CoffeeTooDark_Email1',
                scheduled=now + timedelta(days=7),
                recommended_coffee=recommended_coffee,
            )
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='Just 24 hours remaining to claim a $6 discount',
                template_name='React_Trial_CoffeeTooDark_Email2',
                scheduled=now + timedelta(days=14),
                recommended_coffee=recommended_coffee,
            )
        else:
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='{}, fancy $2 off each of your next three orders?'.format(name),
                template_name='React_Active_CoffeeTooDark_Email1',
                scheduled=now + timedelta(days=7),
                recommended_coffee=recommended_coffee,
            )
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='Just 24 hours remaining to claim a $6 discount',
                template_name='React_Active_CoffeeTooDark_Email2',
                scheduled=now + timedelta(days=14),
                recommended_coffee=recommended_coffee,
            )

    elif reason == "sour":
        recommended_coffee = order.customer.get_recommended_coffee_for_cancellations(order, reason)
        if order_count < 3:
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='{}, fancy $2 off each of your next three orders?'.format(name),
                template_name='React_Trial_CoffeeTooSour_Email1',
                scheduled=now + timedelta(days=7),
                recommended_coffee=recommended_coffee,
            )
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='Just 24 hours remaining to claim a $6 discount',
                template_name='React_Trial_CoffeeTooSour_Email2',
                scheduled=now + timedelta(days=14),
                recommended_coffee=recommended_coffee,
            )
        else:
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='{}, fancy $2 off each of your next three orders?'.format(name),
                template_name='React_Active_CoffeeTooSour_Email1',
                scheduled=now + timedelta(days=7),
                recommended_coffee=recommended_coffee,
            )
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='Just 24 hours remaining to claim a $6 discount',
                template_name='React_Active_CoffeeTooSour_Email2',
                scheduled=now + timedelta(days=14),
                recommended_coffee=recommended_coffee,
            )

    # elif reason == "caffeine":
    #     if order_count < 3:
    #         Reminder.objects.create(
    #             username=name,
    #             email=email,
    #             from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
    #             subject='',
    #             template_name='',
    #             scheduled=now + timedelta(days=1),
    #         )
    #         Reminder.objects.create(
    #             username=name,
    #             email=email,
    #             from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
    #             subject='',
    #             template_name='',
    #             scheduled=now + timedelta(days=5),
    #         )
    #         Reminder.objects.create(
    #             username=name,
    #             email=email,
    #             from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
    #             subject='',
    #             template_name='',
    #             scheduled=now + timedelta(days=7),
    #         )
    #         Reminder.objects.create(
    #             username=name,
    #             email=email,
    #             from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
    #             subject='',
    #             template_name='',
    #             scheduled=now + timedelta(days=14),
    #         )
    #     else:
    #         Reminder.objects.create(
    #             username=name,
    #             email=email,
    #             from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
    #             subject='',
    #             template_name='',
    #             scheduled=now + timedelta(days=1),
    #             # voucher=personal_voucher
    #         )
    #         Reminder.objects.create(
    #             username=name,
    #             email=email,
    #             from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
    #             subject='',
    #             template_name='',
    #             scheduled=now + timedelta(days=5),
    #             # voucher=personal_voucher
    #         )
    #         Reminder.objects.create(
    #             username=name,
    #             email=email,
    #             from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
    #             subject='',
    #             template_name='',
    #             scheduled=now + timedelta(days=7),
    #             # voucher=personal_voucher
    #         )
    #         Reminder.objects.create(
    #             username=name,
    #             email=email,
    #             from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
    #             subject='',
    #             template_name='',
    #             scheduled=now + timedelta(days=14),
    #             # voucher=personal_voucher
    #         )

    elif reason == "expensive":
        if order_count < 3:
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='Just 24 hours remaining to claim a $6 discount',
                template_name='React_Trial _TooExpensiveEmail1',
                scheduled=now + timedelta(days=1),
            )
        else:
            Reminder.objects.create(
                username=name,
                email=email,
                from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
                subject='Just 24 hours remaining to claim a $6 discount',
                template_name='React_Active _TooExpensiveEmail1',
                scheduled=now + timedelta(days=1),
            )

    elif reason == "abroad":
        # Reminder.objects.create(
        #     username=name,
        #     email=email,
        #     from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
        #     subject='Want us to ship your order elsewhere {}?'.format(name),
        #     template_name='React_All_MovingAbroadEmail1',
        #     scheduled=now + timedelta(days=1),
        # )
        pass

    elif reason in ["upset", "other"]:
        Reminder.objects.create(
            username=name,
            email=email,
            from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
            subject='What happened {}?'.format(name),
            template_name='React_All_NoReasonEmail1',
            scheduled=now + timedelta(days=1),
        )

    else:
        Reminder.objects.create(
            username=name,
            email=email,
            from_email='Faye from Hook Coffee <hola@hookcoffee.com.sg>',
            subject='What happened {}?'.format(name),
            template_name='React_All_NoReasonEmail1',
            scheduled=now + timedelta(days=1),
        )


@periodic_task(run_every=(crontab(minute="*/30")))
def send_shopping_cart_reminders():
    ctz = timezone.get_current_timezone()
    now = ctz.normalize(timezone.now())

    carts_1 = ShoppingCart.objects.filter(
        last_modified__lte=now - timedelta(hours=SC_WAITING_TIME_1),
        first_reminder=False,
        second_reminder=False
        )
    carts_2 = ShoppingCart.objects.filter(
        last_modified__lte=now - timedelta(hours=SC_WAITING_TIME_2),
        first_reminder=True,
        second_reminder=False
        )

    [cart.send_first_reminder() for cart in carts_1]
    [cart.send_second_reminder() for cart in carts_2]


@periodic_task(run_every=(crontab(minute="*/30")))
def cleanup_shopping_cart_reminders():
    ctz = timezone.get_current_timezone()
    now = ctz.normalize(timezone.now())

    for cart in ShoppingCart.objects.filter(
        last_modified__lte=now - timedelta(hours=SC_WAITING_TIME_3),
        first_reminder=True,
        second_reminder=True
        ):
        cart.disable_voucher()

    ShoppingCart.objects.empty().delete()


@periodic_task(run_every=(crontab(minute="*/30")))
def deactivate_expired_vouchers():
    ctz = timezone.get_current_timezone()
    now = ctz.normalize(timezone.now())

    for cart in Reminder.objects.filter(
        scheduled__lte=now - timedelta(hours=24),
        template_name__iexact="Activation Stage 4"
        ):
        cart.disable_voucher()

    ShoppingCart.objects.empty().delete()


class SendEmailTask(Task):

    def on_success(self, retval, task_id, args, kwargs):
        attachments = kwargs.get('attachments', [])
        # if the email has the attachments - they will be removed
        for attach in attachments:
            filename, filepath, mimetype = attach
            os.remove(filepath)
        return super(SendEmailTask, self).on_success(retval, task_id, args, kwargs)


@celery_app.task(base=SendEmailTask, bind=True)
def send_email_async(
    self, subject, template, to_email, from_email=DEFAULT_FROM_EMAIL,
    merge_vars=None, metadata=None, attachments=None):

    msg = EmailMessage(
        subject=subject,
        to=[to_email],
        from_email=from_email,
    )
    msg.template_name = template
    msg.merge_vars = {to_email: {'USERNAME': 'there'}}

    if not merge_vars:
        merge_vars = {}

    merge_vars.setdefault('DOMAIN_NAME', 'hookcoffee.com.sg')
    msg.merge_vars[to_email].update(merge_vars)

    if metadata:
        msg.metadata = metadata

    if attachments:
        for attach in attachments:
            filename, filepath, mimetype = attach
            content = open(filepath, 'rb').read()
            msg.attach(filename, content, mimetype)

    try:
        msg.send()
    except Exception as e:
        logger.error('Send email:error tpl: %s, to: %s',
                     template, to_email, exc_info=True)
        raise self.retry(exc=e, countdown=1 * 60)  # retry in a minute
    else:
        logger.debug('Send email:success tpl: %s, to: %s' % (
                     msg.template_name, to_email))


@periodic_task(run_every=(crontab(hour='*/24')))
def mailchimp_update_active_inactive_users_segments():
    list_id = settings.MAILCHIMP_DEFAULT_LIST
    active_segment_id = settings.MAILCHIMP_ACTIVE_SEGMENT
    inactive_segment_id = settings.MAILCHIMP_INACTIVE_SEGMENT

    limit = 1000
    actives = Customer.objects.active()
    inactives = Customer.objects.inactive()

    for i in range(0, actives.count(), limit):
        _actives = actives[i:i+limit]
        payload = [
            {
                'email': cus.user.email.lower()
            } for cus in _actives]

        try:
            m = mailchimp.Mailchimp(apikey=settings.MAILCHIMP_API_KEY)
            # add active users to Active segment
            m.lists.static_segment_members_add(
                id=list_id,
                seg_id=active_segment_id,
                batch=payload,
            )
            # remove active users from Inactive segment
            m.lists.static_segment_members_del(
                id=list_id,
                seg_id=inactive_segment_id,
                batch=payload,
            )
        except mailchimp.Error as e:
            logger.error(
                'Failed to manage active users', exc_info=True)
            raise self.retry(exc=e, countdown=30)

    for i in range(0, inactives.count(), limit):
        _inactives = inactives[i:i+limit]
        payload = [
            {
                'email': cus.user.email.lower()
            } for cus in _inactives]

        try:
            m = mailchimp.Mailchimp(apikey=settings.MAILCHIMP_API_KEY)
            # add inactive users to Inactive segment
            m.lists.static_segment_members_add(
                id=list_id,
                seg_id=inactive_segment_id,
                batch=payload,
            )
            # remove inactive users from Active segment
            m.lists.static_segment_members_del(
                id=list_id,
                seg_id=active_segment_id,
                batch=payload,
            )
        except mailchimp.Error as e:
            logger.error(
                'Failed to manage inactive users', exc_info=True)
            raise self.retry(exc=e, countdown=30)
