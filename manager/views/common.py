# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import sys
from datetime import datetime, timedelta

from braces.views import JSONResponseMixin, JsonRequestResponseMixin

from jsonview.decorators import json_view

from django.contrib.auth import login, logout
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_GET
from django.views.generic import FormView, TemplateView, View

from coffees.models import BrewMethod, CoffeeType

from customers.models import Customer, GearOrder, Order

from .base import BaseApiView
from ..forms import ManagerLoginForm
from ..pdf import addressgenerator, labelgenerator, postcard_generator
from ..utils import get_week, order_count_json


class Index(TemplateView):
    template_name = 'manager/index.html'


class BrewMethods(BaseApiView):

    def get(self, request, *args, **kwargs):
        return self.render_json_response(
            list(BrewMethod.objects.all().values_list('name', flat=True)))


class IsAuthenticated(JSONResponseMixin, View):

    def get(self, request, *args, **kwargs):
        user = request.user
        role = ''
        if user.groups.filter(name='admin').exists():
            role = 'admin'
        elif user.groups.filter(name='packer').exists():
            role = 'packer'
        success = bool(user.is_authenticated and role)
        code = 200 if success else 401
        return self.render_json_response(
            {'success': success, 'role': role}, code)


class ManagerLogin(JsonRequestResponseMixin, JSONResponseMixin, FormView):

    form_class = ManagerLoginForm

    def get_form_kwargs(self):
        kwargs = super(ManagerLogin, self).get_form_kwargs()
        kwargs.update({'request': self.request, 'data': self.request_json})
        return kwargs

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        self.request.session['user'] = user.id  # for backward compatibility
        return self.render_json_response({
            'success': True, 'role': user.groups.get().name})

    def form_invalid(self, form):
        return self.render_json_response({
            'success': False, 'role': None, 'errors': form.errors}, 401)


class ManagerLogout(View):

    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('/manager/')


class OrderLabels(BaseApiView):

    def post(self, request, *args, **kwargs):
        orders = self.request_json['orders']
        return labelgenerator.print_labels(orders)


class OrderAddresses(BaseApiView):

    def post(self, request, *args, **kwargs):
        orders = self.request_json['orders']
        return addressgenerator.print_addresses(orders)


class CustomerAddress(BaseApiView):

    def post(self, request, *args, **kwargs):
        customer_id = self.request_json['customer']
        return addressgenerator.print_address_by_customer(customer_id)


class OrderPostcards(BaseApiView):

    def get_new_customers(self, orders):
        """Return only new customers, for which passed order is first."""
        coffee_orders_ids = []
        gear_orders_ids = []

        for order_id, order_type in orders:
            if order_type == 'GEAR':
                gear_orders_ids.append(order_id)
            elif order_type == 'COFFEE':
                coffee_orders_ids.append(order_id)

        new_customers = []
        all_customers = Customer.objects.filter(
            Q(orders__id__in=coffee_orders_ids) |
            Q(gearorders__id__in=gear_orders_ids)
        ).distinct()

        for customer in all_customers:
            try:
                first_coffee_order = customer.orders.earliest('id').id
            except Order.DoesNotExist:
                first_coffee_order = None
            try:
                first_gear_order = customer.gearorders.earliest('id').id
            except GearOrder.DoesNotExist:
                first_gear_order = None
            if (first_coffee_order in coffee_orders_ids or
                    first_gear_order in gear_orders_ids):
                new_customers.append(customer)
        return new_customers

    def post(self, request, *args, **kwargs):
        orders = self.request_json['orders']
        customers = self.get_new_customers(orders)
        return postcard_generator.print_postcards(customers)


def orderCount(request):
    data = json.loads(request.body)
    try:
        #convert date from String to Date object
        start_date = data['startdate']
        start_date = datetime.strptime(start_date, '%d-%m-%Y').date()

        # convert date from String to Date object
        end_date = data['enddate']
        end_date = datetime.strptime(end_date, "%d-%m-%Y").date()
    except KeyError as e:
        weekdays = [d for d in get_week(datetime.now().date())]
        start_date = weekdays[0]
        end_date = weekdays[6]

    # check whether end date lesser than start date
    if end_date < start_date:
        RESULT_JSON = {}
        RESULT_JSON['error_message'] = 'End date must be greater than the Start Date!'
        RESULT_JSON['status'] = 500
        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    new_end_date = end_date + timedelta(days=1)
    # query for orders
    try:
        order_set = Order.objects.filter(shipping_date__gte=start_date,
                                         shipping_date__lte=new_end_date)
    except Exception as e:
        sys.stderr.write(str(e))

    # check whether there are any orders according to the criteria
    if not order_set.exists():
        RESULT_JSON = {}
        RESULT_JSON['error_message'] = 'No orders are found matching the given criteria'
        RESULT_JSON['status'] = 500
        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    brew_method_filter = data['type']

    orders = order_count_json(start_date, end_date, order_set, brew_method_filter)

    RESULT_JSON = {}
    RESULT_JSON['orders'] = orders
    RESULT_JSON['status'] = 200

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


def get_all_coffee_types(request):
    """
    Returns all coffee types
    :param request:
    :return: JSON containing all coffee types (ID and Name)
    """
    coffees_set = CoffeeType.objects.all()
    coffees = []

    try:
        for coffee in coffees_set:
            coffee_details = {}
            coffee_details['coffee_id'] = coffee.id
            coffee_details['coffee_name'] = coffee.name

            coffees.append(coffee_details)
    except Exception as e:
        sys.stderr.write(str(e))

    coffees = sorted(coffees, key=lambda k: k['coffee_id'])

    RESULT_JSON = {}
    RESULT_JSON['coffees'] = coffees
    RESULT_JSON['status'] = 200

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


def get_available_coffee_types(request):
    """
    Returns all available coffee types
    :param request:
    :return: JSON containing all available coffee types (ID and Name)
    """
    coffees_set = CoffeeType.objects.filter(mode='True')
    coffees = []

    try:
        for coffee in coffees_set:
            coffee_details = {}
            coffee_details['coffee_id'] = coffee.id
            coffee_details['coffee_name'] = coffee.name

            coffees.append(coffee_details)
    except Exception as e:
        sys.stderr.write(str(e))

    coffees = sorted(coffees, key=lambda k: k['coffee_id'])

    RESULT_JSON = {}
    RESULT_JSON['coffees'] = coffees
    RESULT_JSON['status'] = 200

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')
