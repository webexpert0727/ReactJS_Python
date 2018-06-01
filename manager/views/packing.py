# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta
from itertools import chain
from multiprocessing import Lock

from braces.views import SelectRelatedMixin

from django.conf import settings
from django.db.models.query import QuerySet
from django.utils.functional import cached_property
from django.views.generic.detail import SingleObjectMixin

from coffees.models import CoffeeType

from customers.models import GearOrder, Order, Preferences
from customers.tasks import send_email_async

from loyale.models import RedemItem

from .base import BaseApiView
from ..pdf import addressgenerator
from ..utils import (
    OrderProcessing, serialize_orders, parse_datetime,
    customers_with_multiple_orders)


ProcessOrder_LOCK = Lock()


class ProcessOrder(BaseApiView, SingleObjectMixin):
    """Get the order ID when scanning barcode or click `Process` in orders table.

    Updates the order status and returns address label.
    """

    @cached_property
    def model(self):
        self.order_type = self.request_json['orderType'].upper()
        if self.order_type == 'GEAR':
            return GearOrder
        elif self.order_type == 'REDEM':
            return RedemItem
        return Order

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg)
        qs = self.get_queryset().filter(pk=pk)
        select_related_fields = [
            'voucher', 'customer', 'customer__user', 'customer__preferences']
        if self.model is GearOrder:
            qs = qs.select_related(*select_related_fields)
        elif self.model is RedemItem:
            qs = qs.select_related('user__customer')
        else:
            qs = qs.select_related('coffee', 'brew', *select_related_fields)
        return qs.get()

    def dispatch(self, request, *args, **kwargs):
        with ProcessOrder_LOCK:
            return super(ProcessOrder, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if isinstance(obj, RedemItem):
            obj.status = 'done'
            obj.save(update_fields=['status'])
        else:
            request.request_json = self.request_json
            result = OrderProcessing(request, obj).process()
            err = result.get('error')
            if err:
                status = 402 if 'declined' in result else 406
                errmsg = (
                    'An error occurred while processing the order!\n\n'
                    'Order: {pk}\nUsername/Email: {name}\nAccount number: {acc}\n'
                    'Error: {err}').format(pk=obj.pk, name=obj.customer,
                                           acc=obj.customer.stripe_id, err=err)
                return self.render_json_response({'error': errmsg}, status)
        return addressgenerator.print_addresses([(obj.id, self.order_type)])


class CoffeeModalItems(BaseApiView, SelectRelatedMixin, SingleObjectMixin):

    select_related = ['customer', 'voucher']

    @cached_property
    def model(self):
        order_type = self.request.GET['orderType']
        if order_type == 'GEAR':
            return GearOrder
        return Order

    def get(self, request, *args, **kwargs):
        order = self.get_object()
        customer = order.customer
        gifts = set(v for v in settings.GIFT_VOUCHERS if v in order.details)
        if order.voucher and order.voucher.name in settings.GIFT_VOUCHERS:
            gifts.add(order.voucher.name)
        return self.render_json_response({
            'gifts': list(gifts),
            'referredBy': order.details.get('referred_by', ''),
            'coffeesHasntTried': [{'id': c.id, 'name': c.name}
                                  for c in customer.get_coffees_hasnt_tried()],
            'coffeesSampled': list(customer.received_coffee_samples
                                   .all().values_list('name', flat=True)),
            'orderHistory': serialize_orders(customer.orders.all()),
        })


class CoffeesSampled(BaseApiView, SelectRelatedMixin, SingleObjectMixin):

    model = Order
    select_related = ['customer']

    def post(self, request, *args, **kwargs):
        customer = self.get_object().customer
        coffee_sampled_id = self.request_json['coffeeSampledID']
        coffee_sampled = CoffeeType.objects.get(id=coffee_sampled_id)
        customer.received_coffee_samples.add(coffee_sampled)
        return self.render_json_response({}, 200)


class PackingOrders(BaseApiView):

    queryset = None

    def get_queryset(self, date, show_backlog):
        if isinstance(self.queryset, QuerySet):
            return self.queryset.all()

        orders = Order.objects.filter(
            coffee__in=CoffeeType.objects.non_tasters(only_active=False),
            status__in=[Order.ACTIVE, Order.PAUSED],
            shipping_date__lt=date + timedelta(days=2),
            customer__country='SG')
        if not show_backlog:
            orders = orders.filter(shipping_date__gte=date + timedelta(days=1))
        orders = orders.exclude(
            customer__in=customers_with_multiple_orders(date, show_backlog))
        orders = [x for x in orders if not x.coffee.is_bottled()]
        return orders

    def post(self, request, *args, **kwargs):
        context = {}
        date = self.request_json['date']

        if not date:
            return self.render_json_response(
                {'error': 'Please input a date'}, 400)

        date = parse_datetime(date)
        show_backlog = self.request_json['backlog']
        orders = self.get_queryset(date, show_backlog)
        brew_method = self.request_json['brew_method']
        order_by = self.order_by() if hasattr(self, 'order_by') else None
        context['orders'] = serialize_orders(orders, brew_method, order_by)
        return self.render_json_response(context)


class BottledOrders(PackingOrders):

    def get_queryset(self, date, show_backlog):
        if isinstance(self.queryset, QuerySet):
            return self.queryset.all()

        orders = Order.objects.filter(
            coffee__in=CoffeeType.objects.bottled(only_active=False),
            status__in=[Order.ACTIVE, Order.PAUSED],
            shipping_date__lt=date + timedelta(days=2),
            customer__country='SG')
        if not show_backlog:
            orders = orders.filter(shipping_date__gte=date + timedelta(days=1))
        orders = orders.exclude(
            customer__in=customers_with_multiple_orders(date, show_backlog))
        return orders


class TasterPackOrders(PackingOrders):

    def get_queryset(self, date, show_backlog):
        orders = Order.objects.filter(
            coffee__in=CoffeeType.objects.tasters(only_active=False),
            status__in=[Order.ACTIVE, Order.PAUSED],
            shipping_date__lt=date + timedelta(days=2),
            customer__country='SG')
        if not show_backlog:
            orders = orders.filter(shipping_date__gte=date + timedelta(days=1))
        return orders.exclude(
            customer__in=customers_with_multiple_orders(date, show_backlog))


class GearOrders(PackingOrders):

    def get_queryset(self, date, show_backlog):
        orders = GearOrder.objects.filter(
            status__in=[Order.ACTIVE, Order.PAUSED],
            shipping_date__lt=date + timedelta(days=2),
            customer__country='SG')\
                .exclude(gear__special='christmas')
        if not show_backlog:
            orders = orders.filter(shipping_date__gte=date + timedelta(days=1))
        return orders.exclude(
            customer__in=customers_with_multiple_orders(date, show_backlog))


class ChristmasOrders(PackingOrders):

    def get_queryset(self, date, show_backlog):
        orders = GearOrder.objects.filter(
            gear__special='christmas',
            status__in=[Order.ACTIVE, Order.PAUSED],
            shipping_date__lt=date + timedelta(days=2),
            customer__country='SG')
        if not show_backlog:
            orders = orders.filter(shipping_date__gte=date + timedelta(days=1))
        return orders
        # .exclude(
            # customer__in=customers_with_multiple_orders(date, show_backlog))


class UnredeemedItems(PackingOrders):

    def get_queryset(self, date, show_backlog):
        return (
            RedemItem.objects
            .filter(status='pending')
            .exclude(user__customer__in=customers_with_multiple_orders(
                     date, show_backlog)))


class MultipleOrders(PackingOrders):
    """Multiple orders from the customer to be shipped at the same time."""

    def order_by(self):
        return lambda o: (o['customer_id'], o['shipping_date'], o['coffee'])

    def get_queryset(self, date, show_backlog):
        customer_ids = customers_with_multiple_orders(date, show_backlog)
        orders = Order.objects.filter(
            status__in=[Order.ACTIVE, Order.PAUSED],
            shipping_date__lt=date + timedelta(days=2),
            customer__in=customer_ids,
            customer__country='SG')
        gear_orders = GearOrder.objects.filter(
            status__in=[Order.ACTIVE, Order.PAUSED],
            shipping_date__lt=date + timedelta(days=2),
            customer__in=customer_ids,
            customer__country='SG')
        redem_orders = RedemItem.objects.filter(
            status='pending',
            user__customer__in=customer_ids,
            user__customer__country='SG')
        if not show_backlog:
            orders = orders.filter(shipping_date__gte=date + timedelta(days=1))
            gear_orders = gear_orders.filter(shipping_date__gte=date + timedelta(days=1))
        return list(chain(orders, gear_orders, redem_orders))


class DeclinedOrders(PackingOrders):

    queryset = Order.objects.filter(status__in=[Order.DECLINED, Order.ERROR])


class WorldWideCoffeeOrders(PackingOrders):

    def get_queryset(self, date, show_backlog):
        orders = (
            Order.objects
            .filter(status__in=[Order.ACTIVE, Order.PAUSED],
                    shipping_date__lt=date + timedelta(days=2))
            .exclude(customer__country='SG'))
        if not show_backlog:
            orders = orders.filter(shipping_date__gte=date + timedelta(days=1))
        return orders


class WorldWideGearOrders(GearOrders):

    def get_queryset(self, date, show_backlog):
        orders = (
            GearOrder.objects
            .filter(status__in=[Order.ACTIVE, Order.PAUSED],
                    shipping_date__lt=date + timedelta(days=2))
            .exclude(customer__country='SG'))
        if not show_backlog:
            orders = orders.filter(shipping_date__gte=date + timedelta(days=1))
        return orders


class CustomerHasMultipleOrders(BaseApiView, SingleObjectMixin):

    @cached_property
    def model(self):
        order_type = self.request_json['orderType'].upper()
        if order_type == 'GEAR':
            return GearOrder
        elif order_type == 'REDEM':
            return RedemItem
        return Order

    def post(self, request, *args, **kwargs):
        order = self.get_object()
        if isinstance(order, RedemItem):
            customer_id = order.user.customer.id
        else:
            customer_id = order.customer_id
        date = parse_datetime(self.request_json['date'])
        show_backlog = self.request_json['backlog']
        customer_ids = customers_with_multiple_orders(date, show_backlog)
        return self.render_json_response(
            {'has_multiple_orders': customer_id in customer_ids})


class SwitchCoffee(BaseApiView):
    """Switch users to another coffee."""

    EMAIL_SUBJECT = (
        "We hope you don't mind, we'll be sending you something different!")
    EMAIL_TEMPLATE = 'Running out of Coffee'

    def _get_new_amount(self, order, new_coffee):
        """Recalculate amount for the given order."""
        new_amount = (new_coffee.amount if order.recurrent else
                      new_coffee.amount_one_off)
        voucher = order.voucher
        if voucher:
            new_amount = (new_amount - new_amount *
                          voucher.discount / 100 - voucher.discount2)
        return new_amount

    def _update_preferences(self, old_coffee, new_coffee):
        """Change coffee in user Preferences."""
        Preferences.objects.filter(coffee=old_coffee).update(coffee=new_coffee)

    def _update_orders(self, old_coffee, new_coffee):
        """Change coffee and amount in upcoming orders."""
        orders = (Order.objects.filter(coffee=old_coffee)
                               .exclude(status__in=[Order.SHIPPED,
                                                    Order.CANCELED]))
        for order in orders:
            order.coffee = new_coffee
            order.amount = self._get_new_amount(order, new_coffee)
            order.save(update_fields=['coffee', 'amount'])
            # Send email to notify user their coffee has been changed
            send_email_async.delay(
                subject=self.EMAIL_SUBJECT,
                template=self.EMAIL_TEMPLATE,
                to_email=order.customer.get_email(),
                merge_vars={
                    'USERNAME': order.customer.first_name,
                    'OLD_COFFEE': str(old_coffee),
                    'NEW_COFFEE': str(new_coffee),
                    'DOMAIN_NAME': self.request.META.get('HTTP_HOST'),
                }
            )

    def post(self, request, *args, **kwargs):
        context = {}
        coffee_from = self.request_json.get('coffee_from')
        coffee_to = self.request_json.get('coffee_to')

        if not coffee_from or not coffee_to:
            return self.render_json_response(
                {'error': 'Should be selected CoffeeFrom and CoffeeTo!'}, 400)

        try:
            old_coffee = CoffeeType.objects.get(id=coffee_from)
            new_coffee = CoffeeType.objects.get(id=coffee_to)
        except CoffeeType.DoesNotExist:
            return self.render_json_response(
                {'error': 'No coffee was found matching the given ID!'}, 400)

        self._update_preferences(old_coffee, new_coffee)
        self._update_orders(old_coffee, new_coffee)
        context['message'] = 'Coffee type has been changed successfully'
        return self.render_json_response(context)


class ToBeShippedCount(BaseApiView):

    def post(self, request, *args, **kwargs):

        date = self.request_json['date']

        if not date:
            return self.render_json_response(
                {'error': 'Please input a date'}, 400)

        date = parse_datetime(date)
        show_backlog = self.request_json['backlog']

        orders_with_backlogs = Order.objects.filter(
            status__in=[Order.ACTIVE, Order.PAUSED],
            shipping_date__lt=date + timedelta(days=2))
        orders_with_backlogs_count = orders_with_backlogs.count()

        gear_orders_with_backlogs = GearOrder.objects.filter(
            status__in=[Order.ACTIVE, Order.PAUSED],
            shipping_date__lt=date + timedelta(days=2))
        gear_orders_with_backlogs_count = gear_orders_with_backlogs.count()

        orders_without_backlogs = orders_with_backlogs.filter(shipping_date__gte=date + timedelta(days=1))
        orders_without_backlogs_count = orders_without_backlogs.count()

        gear_orders_without_backlogs = gear_orders_with_backlogs.filter(shipping_date__gte=date + timedelta(days=1))
        gear_orders_without_backlogs_count = gear_orders_without_backlogs.count()

        total_orders = orders_with_backlogs_count + gear_orders_with_backlogs_count
        backlogs_count = total_orders - orders_without_backlogs_count - gear_orders_without_backlogs_count

        if not show_backlog:
            total_orders = orders_without_backlogs_count + gear_orders_without_backlogs_count


        return self.render_json_response({
            'orders': total_orders,
            'backlog': backlogs_count,
            })
