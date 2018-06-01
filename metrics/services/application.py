# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals

import json
from datetime import datetime

from dateutil import rrule
from dateutil.relativedelta import relativedelta

from django.utils import timezone

from customers.models import Customer, GearOrder, Order

from get_started.models import ReferralVoucher

from manager.models import IntercomLocal


CTZ = timezone.get_current_timezone()


def customers(customer_id=None):
    result = []
    qs = (
        Customer.objects
        .select_related('user')
        .prefetch_related('vouchers', 'orders')
        .all()
    )
    if customer_id:
        qs = qs.filter(id=customer_id)

    for cus in qs.iterator():
        created_at = cus.user.created_at
        data = {
            'id': cus.id,
            'customer_email': cus.user.email.lower(),
            'name': cus.get_full_name(),
            'phone': cus.phone,
            'address': cus.get_full_address(),
            'postcode': cus.postcode,
            'country': cus.country.code if hasattr(cus.country, 'code') else 'SG',
            'amount': cus.amount,
            'stripe_id': cus.stripe_id,
            'has_shotpods_orders': cus.has_shotpods_orders,
            'is_invited': cus.is_invited,
            'friends_invited': cus.get_friends_invited(),
            'friends_joined': cus.get_friends_joined(),
            'preferred_brew_method': cus.get_preferred_brew_method(),
            # 'total_spend': cus.get_total_spend(),
            'last_login_at': cus.get_last_login(),  # unixtimestamp
            'last_order_status': cus.get_last_order_status(),
            'last_order_date': cus.get_last_order_date(),  # unixtimestamp
            'total_shipped_orders': cus.get_count_orders(),
        }
        tags = {
            'customer_id': cus.user.id,
            'customer_email': cus.user.email.lower(),
            'card_fingerprint': cus.get_last_cardfingerprint(),
        }
        result.append({'date': created_at, 'values': data, 'tags': tags})
    return result


def orders(order_id=None):
    result = []
    qs = (
        Order.objects
        .select_related('customer__user', 'coffee', 'brew', 'voucher')
        .all()
    )
    if order_id:
        qs = qs.filter(id=order_id)

    status_color = {s[0]: i for i, s in enumerate(Order.STATUS_CHOICES)}

    for order in qs.iterator():
        created_at = order.date
        data = {
            'id': order.id,
            'shipping_date': order.shipping_date,
            'status': order.status,
            'status_color': status_color[order.status],
            'different': order.different,
            'amount': order.amount,
            'recurrent': order.recurrent,
            'interval': order.interval,
            'resent': order.resent,
            'custom_price': order.custom_price,
            'voucher_name': order.voucher.name if order.voucher else None,
            'is_first_order': order.is_first_order,
        }
        tags = {
            'customer_id': order.customer.id,
            'customer_email': order.customer.user.email.lower(),
            'coffee_name': order.coffee.name,
            'brew_name': order.brew.name,
            'package': order.package,
            'interval': order.interval,
            'different': order.different,
            'voucher_name': order.voucher.name if order.voucher else None,
        }
        result.append({'date': created_at, 'values': data, 'tags': tags})
    return result


def gear_orders(order_id=None):
    result = []
    qs = (
        GearOrder.objects
        .select_related('customer__user', 'gear', 'voucher')
        .all()
    )
    if order_id:
        qs = qs.filter(id=order_id)

    status_color = {s[0]: i for i, s in enumerate(Order.STATUS_CHOICES)}

    for order in qs.iterator():
        created_at = order.date
        data = {
            'id': order.id,
            'shipping_date': order.shipping_date,
            'status': order.status,
            'status_color': status_color[order.status],
            'amount': order.price,
            'tracking_number': order.tracking_number,
            'voucher_name': order.voucher.name if order.voucher else None,
        }
        tags = {
            'customer_id': order.customer.id,
            'customer_email': order.customer.user.email.lower(),
            'gear_name': order.gear.name,
            'voucher_name': order.voucher.name if order.voucher else None,
        }
        result.append({'date': created_at, 'values': data, 'tags': tags})
    return result


def events(customer_id=None):
    result = []
    qs = IntercomLocal.objects.select_related('customer__user').all()
    if customer_id:
        qs = qs.filter(customer_id=customer_id)

    for event in qs.iterator():
        created_at = event.added_timestamp
        data = {
            'id': event.id,
            'customer': event.customer.id,
            'event': event.event,
            'data': json.dumps(event.data),
        }
        tags = {
            'customer_id': event.customer.id,
            'customer_email': event.customer.user.email.lower(),
            # 'coffee_id': order.coffee.id,
            # 'coffee_name': order.coffee.name,
        }
        result.append({'date': created_at, 'values': data, 'tags': tags})
    return result


def k_factor():
    """K-Factor = (invites / users) * (joined / invites)."""
    result = []
    first_invite_date = ReferralVoucher.objects.earliest('date').date.date()
    from_date = datetime(
        first_invite_date.year,
        first_invite_date.month,
        first_invite_date.day + 1,
        tzinfo=CTZ)
    to_date = datetime.now(tz=CTZ)
    dates = list(rrule.rrule(
        freq=rrule.DAILY, dtstart=from_date, until=to_date))
    time_delta = relativedelta(days=+1)

    qs = Customer.objects.all()
    customer_invited = {cus.id: cus.is_invited for cus in qs.iterator()}

    for date in dates:
        invites = (
            ReferralVoucher.objects
            .filter(date__lt=date + time_delta).count())
        customers = (
            Customer.objects
            .filter(user__created_at__lt=date + time_delta)
            .values_list('id', flat=True))
        users = len(customers)
        joined = sum([customer_invited[cid] for cid in customers])
        value = (invites / users) * (joined / invites)
        data = {
            'invites': invites,
            'users': users,
            'joined': joined,
            'value': value,
        }
        result.append({'date': date, 'values': data, 'tags': {}})
    return result


def invites(invite_id=None):
    result = []
    qs = ReferralVoucher.objects.select_related('sender', 'sender__user').all()
    if invite_id:
        qs = qs.filter(id=invite_id)

    for voucher in qs.iterator():
        created_at = voucher.date
        data = {
            'id': voucher.id,
        }
        tags = {
            'customer_id': voucher.sender.id,
            'customer_email': voucher.sender.user.email.lower(),
        }
        result.append({'date': created_at, 'values': data, 'tags': tags})
    return result
