# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import time
from datetime import datetime, timedelta
from decimal import Decimal
from multiprocessing import Lock, current_process
from multiprocessing.pool import Pool
from threading import Timer

from mock import patch

import pytest

import stripe

from django.utils import timezone

from coffees.factories import BrewMethodFactory

from customers.factories import (
    CustomerFactory, GearOrderFactory, OrderFactory, VoucherFactory)
from customers.models import Order
from manager.utils.order_processing import ordinal
from giveback_project.helpers import get_estimated_date

from loyale.factories import RedemItemFactory
from loyale.models import GrantPointLog, OrderPoints, Point

from manager.utils import OrderProcessing
from manager.views.packing import ProcessOrder

from reminders.models import Reminder


CTZ = timezone.get_current_timezone()


@pytest.fixture()
def request_mock(mocker):
    request = mocker.Mock()
    request.request_json = {}
    request.META = {'HTTP_HOST': 'testserver'}
    return request


def _raise_card_was_declined(*args, **kwargs):
    raise stripe.error.CardError(
        message='Your card was declined.',
        param='number',
        code='card_declined',
        json_body={'error': {'message': 'Your card was declined.'}})


def _pool_init(l):
    global lock
    lock = l


def _run_concurrent_order_processing(args):
    """Helper function for multiprocessing tests."""
    def create_charge(*args, **kwargs):
        if current_process().name == 'PoolWorker-1':
            time.sleep(0.5)
        return {'id': 'ch_0001'}
    rf, admin_user, order = args
    lock.acquire()
    Timer(0.1, lock.release).start()
    with patch('stripe.Charge.create', side_effect=create_charge):
        request = rf.post('/manager/api/commands/processOrder/%d' % order.id,
                          json.dumps({'orderType': 'COFFEE'}),
                          content_type='application/json')
        request.user = admin_user
        response = ProcessOrder.as_view()(request, **{'pk': order.id})
    return response

#
#      TESTS BASE PROCESSING API
#


def test_api_unauthorized(mocker, json_client):
    order = OrderFactory()
    assert order.status == order.ACTIVE
    processing_mock = mocker.patch('manager.utils.OrderProcessing.process')
    resp = json_client.post(
        '/manager/api/commands/processOrder/%d' % order.id,
        {'orderType': 'COFFEE'})
    processing_mock.assert_not_called()
    order.refresh_from_db()
    assert order.status == order.ACTIVE
    assert resp.status_code == 302
    assert '/manager?next=/' in resp.url


def test_api_sub_coffee_order(charge_mock, admin_json_client):
    order = OrderFactory(recurrent=True, amount=14.25)
    assert order.status == order.ACTIVE
    resp = admin_json_client.post(
        '/manager/api/commands/processOrder/%d' % order.id,
        {'orderType': 'COFFEE'})
    charge_mock.assert_called_once_with(
        amount=1425,
        currency='SGD',
        customer=order.customer.stripe_id,
        description=str(order.coffee),
        metadata={'order_id': order.id})
    order.refresh_from_db()
    assert order.status == order.SHIPPED
    assert resp.status_code == 200
    assert resp.content.startswith(b'%PDF')


def test_api_sub_coffee_order_declined(charge_mock, admin_json_client):
    charge_mock.side_effect = _raise_card_was_declined
    order = OrderFactory(recurrent=True, amount=14.25)
    assert order.status == order.ACTIVE
    resp = admin_json_client.post(
        '/manager/api/commands/processOrder/%d' % order.id,
        {'orderType': 'COFFEE'})
    charge_mock.assert_called_once_with(
        amount=1425,
        currency='SGD',
        customer=order.customer.stripe_id,
        description=str(order.coffee),
        metadata={'order_id': order.id})
    order.refresh_from_db()
    assert order.status == Order.DECLINED
    assert resp.status_code == 402
    error = ('An error occurred while processing the order!\n\n'
             'Order: {pk}\nUsername/Email: {name}\nAccount number: {acc}\n'
             'Error: {err}').format(
                 pk=order.pk, name=order.customer,
                 acc=order.customer.stripe_id,
                 err='Your card was declined.')
    assert resp.json() == {'error': error}


def test_api_sub_coffee_order_unexpected_error(charge_mock, admin_json_client):
    charge_mock.side_effect = Exception('Error that will never occur ;)')
    order = OrderFactory(recurrent=True, amount=14.25)
    assert order.status == order.ACTIVE
    resp = admin_json_client.post(
        '/manager/api/commands/processOrder/%d' % order.id,
        {'orderType': 'COFFEE'})
    charge_mock.assert_called_once_with(
        amount=1425,
        currency='SGD',
        customer=order.customer.stripe_id,
        description=str(order.coffee),
        metadata={'order_id': order.id})
    order.refresh_from_db()
    assert order.status == Order.ERROR
    assert resp.status_code == 406
    error = ('An error occurred while processing the order!\n\n'
             'Order: {pk}\nUsername/Email: {name}\nAccount number: {acc}\n'
             'Error: {err}').format(
                 pk=order.pk, name=order.customer,
                 acc=order.customer.stripe_id,
                 err=("Critical Stripe error: "
                      "Exception(u'Error that will never occur ;)',)"))
    assert resp.json() == {'error': error}


def test_api_one_coffee_order(charge_mock, admin_json_client):
    order = OrderFactory(id=18052)
    assert order.status == order.ACTIVE
    resp = admin_json_client.post(
        '/manager/api/commands/processOrder/%d' % order.id,
        {'orderType': 'COFFEE'})
    charge_mock.assert_not_called()
    order.refresh_from_db()
    assert order.status == order.SHIPPED
    assert resp.status_code == 200
    assert resp.content.startswith(b'%PDF')


def test_api_gear_order(charge_mock, admin_json_client):
    order = GearOrderFactory()
    assert order.status == order.ACTIVE
    resp = admin_json_client.post(
        '/manager/api/commands/processOrder/%d' % order.id,
        {'orderType': 'GEAR', 'trackingNumber': 'SG00001'})
    charge_mock.assert_not_called()
    order.refresh_from_db()
    assert order.status == order.SHIPPED
    assert order.tracking_number == 'SG00001'
    assert resp.status_code == 200
    assert resp.content.startswith(b'%PDF')


def test_api_redem_item(mocker, admin_json_client):
    redem = RedemItemFactory()
    assert redem.status == 'pending'
    processing_mock = mocker.patch('manager.utils.OrderProcessing.process')
    resp = admin_json_client.post(
        '/manager/api/commands/processOrder/%d' % redem.id,
        {'orderType': 'REDEM'})
    processing_mock.assert_not_called()
    redem.refresh_from_db()
    assert redem.status == 'done'
    assert resp.status_code == 200
    assert resp.content.startswith(b'%PDF')


#
#      TESTS HANDLER's INITIAL STATE
#


def test_initial_original_status(request_mock):
    order = OrderFactory(status=Order.ACTIVE)
    assert OrderProcessing(request_mock, order).original_status == 'Active'


@pytest.mark.parametrize('_factory,_bool', [
    (OrderFactory, False),
    (GearOrderFactory, True),
])
def test_initial_is_gear(request_mock, _factory, _bool):
    order = _factory()
    assert OrderProcessing(request_mock, order).is_gear is _bool


@pytest.mark.parametrize('brew,_bool', [
    ('Espresso', False),
    ('None', False),
    ('Nespresso', True),
])
def test_initial_is_shotpods(request_mock, brew, _bool):
    order = OrderFactory(brew=BrewMethodFactory(name=brew))
    assert OrderProcessing(request_mock, order).is_shotpods is _bool


@pytest.mark.parametrize('recurrent', [True, False])
def test_initial_customer_is_subscriber(request_mock, recurrent):
    order = OrderFactory(recurrent=recurrent)
    assert (OrderProcessing(request_mock, order)
            .customer_is_subscriber is recurrent)


@pytest.mark.parametrize('shippped_count,is_first', [(0, True), (1, False)])
def test_initial_is_first(request_mock, shippped_count, is_first):
    customer = CustomerFactory()
    for n in range(shippped_count):
        OrderFactory(customer=customer, status=Order.SHIPPED)
    order = OrderFactory(customer=customer)
    handler = OrderProcessing(request_mock, order)
    assert handler.is_first is is_first


def test_shipping_date_exceeding_3_following_days(request_mock, charge_mock):
    now = CTZ.normalize(timezone.now())
    order = OrderFactory(shipping_date=now + timedelta(days=3.1))
    result = OrderProcessing(request_mock, order).process()
    charge_mock.assert_not_called()
    error = 'The order has the shipping date exceeding 3 following days.'
    assert error in result['error']


@pytest.mark.parametrize('status,error', [
    (Order.ACTIVE, None),
    (Order.PAUSED, None),
    (Order.DECLINED, None),
])
def test_order_correct_status(request_mock, charge_mock, status, error):
    order = OrderFactory(status=status)
    result = OrderProcessing(request_mock, order).process()
    charge_mock.assert_called_once()
    assert result.get('error') is error


@pytest.mark.parametrize('status,error', [
    (Order.SHIPPED, 'The order is already processed!'),
    (Order.CANCELED, ('You can only process orders that '
                      'are ACTIVE, PAUSED or DECLINED.')),
    (Order.ERROR, ('You can only process orders that '
                   'are ACTIVE, PAUSED or DECLINED.')),
])
def test_order_has_wrong_status(request_mock, charge_mock, status, error):
    order = OrderFactory(status=status)
    result = OrderProcessing(request_mock, order).process()
    charge_mock.assert_not_called()
    assert result['error'] == error


def test_gear_order_tracking_num(request_mock):
    order = GearOrderFactory()
    tracking_number = '12345'
    request_mock.request_json = {'trackingNumber': tracking_number}
    OrderProcessing(request_mock, order).process()
    assert order.tracking_number == tracking_number


#
#      TESTS CHARGING CUSTOMERS
#


def test_gear_charge(request_mock, charge_mock):
    order = GearOrderFactory()
    result = OrderProcessing(request_mock, order).process()
    order.refresh_from_db()
    charge_mock.assert_not_called()
    assert order.status == Order.SHIPPED
    assert 'error' not in result


@pytest.mark.parametrize('pk,assert_func', [
    (18051, 'assert_called_once'),
    (18052, 'assert_not_called'),
])
def test_order_not_recurrent_charge(request_mock, charge_mock, pk, assert_func):
    order = OrderFactory(id=pk, recurrent=False)
    result = OrderProcessing(request_mock, order).process()
    order.refresh_from_db()
    getattr(charge_mock, assert_func)()
    assert order.status == Order.SHIPPED
    assert 'error' not in result


def test_process_order_as_present(request_mock, charge_mock):
    order = OrderFactory(
        recurrent=True, customer__preferences__present_next=True)
    result = OrderProcessing(request_mock, order).process()
    order.refresh_from_db()
    charge_mock.assert_not_called()
    assert order.customer.preferences.present_next is False
    assert result['processed_by'] == 'present'
    assert order.status == Order.SHIPPED
    assert order.amount == 0


def test_process_order_by_credits(request_mock, charge_mock):
    order = OrderFactory(recurrent=True, amount=20, customer__amount=25)
    result = OrderProcessing(request_mock, order).process()
    order.refresh_from_db()
    charge_mock.assert_not_called()
    assert order.status == Order.SHIPPED
    assert result['processed_by'] == 'credits'
    assert order.customer.amount == 5
    assert order.amount == 0


def test_process_order_by_charge_and_credits(request_mock, charge_mock):
    order = OrderFactory(recurrent=True, amount=20, customer__amount=5)
    result = OrderProcessing(request_mock, order).process()
    order.refresh_from_db()
    charge_mock.assert_called_once_with(
        amount=1500,
        currency='SGD',
        customer=order.customer.stripe_id,
        description=str(order.coffee),
        metadata={'order_id': order.id})
    assert order.status == Order.SHIPPED
    assert result['processed_by'] == 'card'
    assert order.customer.amount == 0
    assert order.amount == 15


def test_process_order_by_charge_and_credits_declined(request_mock, charge_mock):
    charge_mock.side_effect = _raise_card_was_declined
    order = OrderFactory(recurrent=True, amount=20, customer__amount=5)
    result = OrderProcessing(request_mock, order).process()
    order.refresh_from_db()
    order.customer.refresh_from_db()
    charge_mock.assert_called_once_with(
        amount=1500,
        currency='SGD',
        customer=order.customer.stripe_id,
        description=str(order.coffee),
        metadata={'order_id': order.id})
    assert order.status == Order.DECLINED
    assert result.get('processed_by') is None
    # after a declined payment, the amount of credits on customer's account
    # and the order amount needs to be restored to its original value
    assert order.customer.amount == 5
    assert order.amount == 20


def test_process_order_by_charge(request_mock, charge_mock):
    order = OrderFactory(amount=14.15, recurrent=True)
    result = OrderProcessing(request_mock, order).process()
    order.refresh_from_db()
    charge_mock.assert_called_once_with(
        amount=1415,
        currency='SGD',
        customer=order.customer.stripe_id,
        description=str(order.coffee),
        metadata={'order_id': order.id})
    assert order.status == Order.SHIPPED
    assert result['processed_by'] == 'card'


def test_process_order_by_charge_declined(charge_mock, request_mock, mailoutbox):
    charge_mock.side_effect = _raise_card_was_declined
    order = OrderFactory(recurrent=True)
    result = OrderProcessing(request_mock, order).process()
    order.refresh_from_db()
    charge_mock.assert_called_once()
    assert order.status == Order.DECLINED
    assert result.get('processed_by') is None
    assert result['declined'] is True
    assert result['error'] == 'Your card was declined.'

    # check email which sent when card was declined
    assert len(mailoutbox) == 1
    m = mailoutbox[0]
    assert m.subject == OrderProcessing.EMAIL_DECLINED_SUBJECT
    assert m.template_name == OrderProcessing.EMAIL_DECLINED_SUBJECT
    assert m.from_email == 'Hook Coffee <hola@hookcoffee.com.sg>'
    assert list(m.to) == [order.customer.user.email]


def test_process_order_by_charge_unexpected_error(charge_mock, request_mock):
    charge_mock.side_effect = Exception('Error that will never occur ;)')
    order = OrderFactory(recurrent=True)
    result = OrderProcessing(request_mock, order).process()
    order.refresh_from_db()
    charge_mock.assert_called_once()
    assert order.status == Order.ERROR
    assert result.get('processed_by') is None
    assert result['error'] == (
        "Critical Stripe error: Exception(u'Error that will never occur ;)',)")


@pytest.mark.parametrize('_factory,event,order_id', [
    (OrderFactory, 'order-processed', 1000),
    (GearOrderFactory, 'gear-order-processed', None),
])
def test_intercom_event(request_mock, add_event_mock, _factory, event, order_id):
    data = {'old_status': 'Active', 'new_status': 'Shipped', 'error': None}
    if order_id:
        order = _factory(id=order_id)
    else:
        order = _factory()
        data.update({'gear-order': order.id})
    result = OrderProcessing(request_mock, order).process()
    data.update({'stripe_charge': result.get('charge', {}).get('id')})
    add_event_mock.assert_called_once_with(
        customer_id=order.customer.id, event=event,
        order_id=order_id, data=data)


@pytest.mark.parametrize('param', ['bag_sub_special', 'pod_sub_special'])
def test_order_amount_decrease_after_special_to_usual(request_mock, param):
    order = OrderFactory(**{param: True})
    OrderProcessing(request_mock, order).process()
    new_order = order.customer.orders.exclude(id=order.id).get()
    assert new_order.recurrent is True
    assert new_order.amount < order.amount
    assert new_order.amount == Decimal('14')


@pytest.mark.parametrize('param,key', [
    ('bag_sub_special', 'sub_special'),
    ('bag_one_special', 'one_special'),
    ('bag_sub', 'sub_regular'),
    ('bag_one', 'one_regular'),
    ('pod_sub_special', 'sub_special'),  # * no have special for pods
    ('pod_one_special', 'one_special'),  # * no have special for pods
    ('pod_sub', 'sub_pod'),
    ('pod_one', 'one_pod'),
])
def test_grant_points(request_mock, param, key):
    orderPoints = OrderPoints.objects.values().latest('id')
    order = OrderFactory(**{param: True})
    user = order.customer.user
    OrderProcessing(request_mock, order).process()
    user_point = Point.objects.get(user=user)
    log = GrantPointLog.objects.get(user=user)
    assert user_point.points == orderPoints[key]
    assert log.points == orderPoints[key]


#
#       TESTS NEXT ORDER
#


def test_next_order_if_gear(mocker, request_mock):
    order = GearOrderFactory()
    customer = order.customer
    mocker.spy(OrderProcessing, 'create_next_order')
    OrderProcessing(request_mock, order).process()
    assert OrderProcessing.create_next_order.call_count == 0
    assert customer.gearorders.exclude(id=order.id).count() == 0
    assert customer.orders.all().count() == 0  # no new order


def test_next_order_if_not_recurrent(request_mock):
    order = OrderFactory(recurrent=False)
    OrderProcessing(request_mock, order).process()
    assert order.customer.orders.exclude(id=order.id).count() == 0


@pytest.mark.parametrize('stripe_id,orders', [('cus_XXXXX', 1), ('', 0)])
def test_next_order_processed_by_card(mocker, request_mock, stripe_id, orders):
    order = OrderFactory(recurrent=True, customer__stripe_id=stripe_id)
    mocker.spy(OrderProcessing, 'create_next_order')
    OrderProcessing(request_mock, order).process()
    assert OrderProcessing.create_next_order.call_count == 1
    assert order.customer.orders.exclude(id=order.id).count() == orders


def test_next_order_processed_by_present(mocker, request_mock):
    order = OrderFactory(
        recurrent=True, customer__preferences__present_next=True)
    mocker.spy(OrderProcessing, 'create_next_order')
    OrderProcessing(request_mock, order).process()
    assert OrderProcessing.create_next_order.call_count == 1
    assert order.customer.orders.exclude(id=order.id).count() == 1  # new order


@pytest.mark.parametrize('credits,result', [(11, 1), (10, 0)])
def test_next_order_processed_by_credits(mocker, request_mock, credits, result):
    order = OrderFactory(amount=10, recurrent=True, customer__amount=credits)
    mocker.spy(OrderProcessing, 'create_next_order')
    OrderProcessing(request_mock, order).process()
    assert OrderProcessing.create_next_order.call_count == 1
    assert order.customer.orders.exclude(id=order.id).count() == result


@pytest.mark.parametrize('voucher,next_voucher,result', [
    ('THREE20', 'THREE20', Decimal('11.2')),
    ('REFRESH50', None, Decimal('14')),
])
def test_next_order_with_voucher(request_mock, voucher, next_voucher, result):
    order = OrderFactory(amount=14, recurrent=True, voucher=VoucherFactory(
        name=voucher, discount=20))
    OrderProcessing(request_mock, order).process()
    new_order = order.customer.orders.exclude(id=order.id).get()
    assert new_order.amount == result
    if next_voucher:
        assert new_order.voucher.name == next_voucher


@pytest.mark.parametrize('details,result', [
    ({'force_base_address': True}, 'true'),
    ({}, None),
])
def test_next_order_force_base_address(request_mock, details, result):
    order = OrderFactory(recurrent=True, details=details)
    OrderProcessing(request_mock, order).process()
    new_order = order.customer.orders.exclude(id=order.id).get()
    assert new_order.details.get('force_base_address') == result


@pytest.mark.parametrize('param', ['bag_sub', 'pod_sub'])
def test_next_order_same_coffee_if_not_diff(request_mock, param):
    order = OrderFactory(**{param: True})
    OrderProcessing(request_mock, order).process()
    new_order = order.customer.orders.exclude(id=order.id).get()
    assert new_order.coffee == order.coffee


@pytest.mark.parametrize('param', ['bag_sub', 'pod_sub'])
def test_next_order_diff_coffee_if_diff(request_mock, param):
    order = OrderFactory(different=True, **{param: True})
    OrderProcessing(request_mock, order).process()
    new_order = order.customer.orders.exclude(id=order.id).get()
    assert new_order.coffee != order.coffee


@pytest.mark.parametrize('param', ['bag_sub_special', 'pod_sub_special'])
def test_next_order_diff_coffee_if_special(request_mock, param):
    order = OrderFactory(**{param: True})
    OrderProcessing(request_mock, order).process()
    new_order = order.customer.orders.exclude(id=order.id).get()
    assert new_order.coffee != order.coffee
    assert new_order.coffee.special is False
    assert new_order.coffee.mode is True


def test_next_order_coffee_if_discovery_pack(request_mock):
    order = OrderFactory(discovery_pack=True)
    OrderProcessing(request_mock, order).process()
    new_order = order.customer.orders.exclude(id=order.id).get()
    assert new_order.coffee == order.coffee
    assert (new_order.get_discovery_coffee_ids() !=
            order.get_discovery_coffee_ids())


@pytest.mark.parametrize('next_order,expected', [
    ('pod_sub_special', True),
    ('pod_sub', True),
    ('bag_sub_special', False),
    ('bag_sub', False),
])
def test_next_order_decaf(request_mock, next_order, expected):
    f_order = OrderFactory(pod_sub_decaf=True, status=Order.SHIPPED)
    customer = f_order.customer
    for _ in range(30):
        order = OrderFactory(
            customer=customer, different=True, **{next_order: True})
        OrderProcessing(request_mock, order).process()
    assert (customer.orders
            .filter(status=Order.ACTIVE, coffee__decaf=True)
            .exclude(id=f_order.id)
            .exists()) is expected


def test_next_order_same_params(request_mock):
    order = OrderFactory(interval=8, recurrent=True, different=False)
    OrderProcessing(request_mock, order).process()
    new_order = order.customer.orders.exclude(id=order.id).get()
    assert new_order.status == Order.ACTIVE
    attrs = ['coffee', 'amount', 'customer', 'recurrent', 'brew',
             'package', 'different', 'interval']
    for attr in attrs:
        assert getattr(new_order, attr) == getattr(order, attr)


@pytest.mark.parametrize('interval,date', [
    (0, datetime(2000, 1, 3).date()),   # Mon
    (1, datetime(2000, 1, 3).date()),   # Mon
    (2, datetime(2000, 1, 3).date()),   # Mon
    (3, datetime(2000, 1, 4).date()),   # Tue
    (4, datetime(2000, 1, 5).date()),   # Wed
    (5, datetime(2000, 1, 6).date()),   # Thu
    (6, datetime(2000, 1, 7).date()),   # Fri
    (7, datetime(2000, 1, 10).date()),  # Mon
    (8, datetime(2000, 1, 10).date()),  # Mon
    (9, datetime(2000, 1, 10).date()),  # Mon
])
def test_next_order_shipping_date(mocker, request_mock, interval, date):
    dt = datetime(2000, 1, 1, tzinfo=CTZ)  # Saturday
    order = OrderFactory(interval=interval, recurrent=True, different=True,
                         date=dt, shipping_date=dt)
    mocker.patch('django.utils.timezone.now', return_value=dt)
    OrderProcessing(request_mock, order).process()
    new_order = order.customer.orders.exclude(id=order.id).get()
    assert new_order.shipping_date.date() == date


def test_concurrent_order_processing(rf, admin_user):
    order = OrderFactory(recurrent=True)
    pool = Pool(processes=2, initializer=_pool_init, initargs=[Lock()])
    responses = pool.map(_run_concurrent_order_processing, [
        (rf, admin_user, order),
        (rf, admin_user, order),
    ])
    pool.close()
    pool.join()
    error = json.loads(responses[1].content)['error']
    assert 'The order is already processed!' in error
    assert order.customer.orders.filter(status=Order.SHIPPED).count() == 1
    assert order.customer.orders.filter(status=Order.ACTIVE).count() == 1


#
#       TESTS SUMMARY EMAIL
#


def test_summary_email_gear(mocker, request_mock, mailoutbox):
    order = GearOrderFactory()
    summary_email_mock = mocker.patch(
        'manager.utils.OrderProcessing.send_summary_email')
    OrderProcessing(request_mock, order).process()
    summary_email_mock.assert_not_called()
    assert len(mailoutbox) == 0


def test_summary_email_if_resent(request_mock, mailoutbox):
    order = OrderFactory(resent=True)
    OrderProcessing(request_mock, order).process()
    assert len(mailoutbox) == 0


@pytest.mark.parametrize('shippped,credits,sender,subject,template', [
    (0, 0, OrderProcessing.EMAIL_SUMMARY_FROM_FIRST_BAG,
           OrderProcessing.EMAIL_SUMMARY_SUBJECT_FIRST_BAG,
           OrderProcessing.EMAIL_SUMMARY_TEMPLATE_FIRST_BAG),
    (1, 0, OrderProcessing.EMAIL_SUMMARY_FROM,
           OrderProcessing.EMAIL_SUMMARY_SUBJECT,
           OrderProcessing.EMAIL_SUMMARY_TEMPLATE_NORMAL),
    (1, 11, OrderProcessing.EMAIL_SUMMARY_FROM,
            OrderProcessing.EMAIL_SUMMARY_SUBJECT,
            OrderProcessing.EMAIL_SUMMARY_TEMPLATE_NORMAL),
    (1, 10, OrderProcessing.EMAIL_SUMMARY_FROM,
            OrderProcessing.EMAIL_SUMMARY_SUBJECT,
            OrderProcessing.EMAIL_SUMMARY_TEMPLATE_LAST_BAG),
])
def test_summary_email(request_mock, mailoutbox, shippped,
                       credits, sender, subject, template):
    customer = CustomerFactory(amount=credits)
    for n in range(shippped):
        OrderFactory(customer=customer, status=Order.SHIPPED)
    order = OrderFactory(amount=10, customer=customer)
    OrderProcessing(request_mock, order).process()
    assert len(mailoutbox) == 1
    m = mailoutbox[0]
    assert m.from_email == sender
    assert m.subject == subject
    assert m.template_name == template


@pytest.mark.parametrize('brew,package,sent_brew,sent_package', [
    ('Nespresso', 'GR', 'Nespresso®', 'Nespresso® compatible pods'),
    ('Nespresso', 'WB', 'Nespresso®', 'Nespresso® compatible pods'),
    ('Nespresso', 'DR', 'Nespresso®', 'Nespresso® compatible pods'),
    ('Espresso', 'GR', 'Espresso', 'Ground for Espresso'),
    ('Espresso', 'WB', 'Espresso', 'Wholebeans'),
    ('Espresso', 'DR', 'Espresso', 'Drip bags'),
])
def test_summary_email_merge_vars(mocker, request_mock, mailoutbox,
                                  brew, package, sent_brew, sent_package):
    dt = datetime(2020, 1, 1, tzinfo=CTZ)
    mocker.patch('django.utils.timezone.now', return_value=dt)
    order = OrderFactory(amount=18, date=dt, shipping_date=dt,
                         brew=BrewMethodFactory(name=brew), package=package)
    order.coffee.roasted_on = dt
    OrderProcessing(request_mock, order).process()
    assert len(mailoutbox) == 1
    m = mailoutbox[0]
    assert m.from_email == OrderProcessing.EMAIL_SUMMARY_FROM_FIRST_BAG
    assert list(m.to) == [order.customer.user.email]
    assert m.merge_vars == {order.customer.user.email: {
        'COFFEE': order.coffee.name,
        'ROASTED_ON': datetime.strftime(
            order.coffee.roasted_on, '%d/%m/%y'),
        'BREW': sent_brew,
        'PACKAGE': sent_package,
        'PRICE': 'S$ %d' % order.amount,
        'SHIPPING_DATE': '%s %s' % (
            ordinal(order.shipping_date.day),
            datetime.strftime(order.shipping_date, '%B %Y')),
        'ADDRESS_NAME': order.shipping_address['name'],
        'LINE1': order.shipping_address['line1'],
        'COUNTRY_POSTCODE': order.shipping_address['postcode'],
        'NEXT_DELIVERY': datetime.strftime(
            order.shipping_date + timedelta(days=order.interval), '%d %B %Y'),
        'POINTS': 50,
        'TOTAL_POINTS': 50,
        'ESTIMATED_DELIVERY': get_estimated_date(order.shipping_date),
        'REFERRAL_CODE': order.customer.user.referral_set.get().code,
        'DOMAIN_NAME': 'testserver',
        'USERNAME': order.customer.first_name,
    }}


#
#       TESTS REMINDERS
#


def test_remidenrs_if_gear(request_mock):
    order = GearOrderFactory()
    OrderProcessing(request_mock, order).process()
    assert Reminder.objects.all().count() == 0


def test_remidenrs_if_first(mocker, request_mock):
    dt = datetime(2020, 1, 1, tzinfo=CTZ)
    mocker.patch('django.utils.timezone.now', return_value=dt)
    order = OrderFactory()
    customer = order.customer
    OrderProcessing(request_mock, order).process()
    reminder = Reminder.objects.get()
    assert reminder.username == customer.first_name.upper()
    assert reminder.email == customer.user.email
    assert reminder.from_email == 'Faye from Hook Coffee <hola@hookcoffee.com.sg>'
    assert reminder.subject == 'Welcome to Hook Rewards'
    assert reminder.template_name == 'O3 - Welcome to Hook Rewards (done)'
    assert reminder.scheduled == dt + timedelta(days=5)


def test_remidenrs_if_second_and_next(request_mock):
    first_order = OrderFactory(status=Order.SHIPPED)
    customer = first_order.customer
    OrderFactory(customer=customer, status=Order.SHIPPED)
    order = OrderFactory(customer=customer)
    OrderProcessing(request_mock, order).process()
    assert Reminder.objects.all().count() == 0
