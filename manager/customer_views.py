import sys

import datetime
import pytz
import time
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
import json

from coffees.models import CoffeeType, BrewMethod, Flavor
from customauth.models import MyUser
from customers.models import Customer, Order, Preferences, Voucher
from manager.authentication import adminOnly
from manager.utils import send_replacement_email, getNextShippingDate


def get_all_customers(request):
    customers_set = Customer.objects.all()
    customers = []

    try:
        for customer in customers_set:
            customer_details = {}
            customer_details['customer_id'] = customer.id
            full_name = customer.first_name.capitalize() + ' ' + customer.last_name.capitalize()
            customer_details['customer_name'] = full_name
            customer_details['customer_email'] = customer.user.email

            customers.append(customer_details)

    except Exception as e:
        sys.stderr.write(str(e))

    customers = sorted(customers, key=lambda k: k['customer_name'])

    RESULT_JSON = {}
    RESULT_JSON['customers'] = customers
    RESULT_JSON['status'] = 200

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


def customerOrders(request):

    #JSON output
    RESULT_JSON = {}
    orders = []
    errors = []

    #retrieve customer and customer's orders by customer_id
    data = json.loads(request.body)
    customer_id = int(data['customer_id'])

    try:
        customer = Customer.objects.get(id=customer_id)
        orders_set = Order.objects.filter(customer_id=customer_id)
    except ObjectDoesNotExist as e:
        errors.append(str(e))

    if errors:
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = errors
        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    full_name = customer.first_name + ' ' + customer.last_name
    email = customer.user.email

    settings_time_zone = pytz.timezone(settings.TIME_ZONE)

    for order in orders_set:
        created_date = order.date
        created_date = created_date.astimezone(settings_time_zone)

        shipping_date = order.shipping_date
        shipping_date = shipping_date.astimezone(settings_time_zone)

        order_details = {}
        order_details['order_id'] = order.id
        order_details['coffee'] = order.coffee.name
        order_details['brew_method'] = order.brew.name
        order_details['packaging_method'] = order.package
        order_details['created_date'] = time.mktime(created_date.timetuple())
        order_details['shipping_date'] = time.mktime(shipping_date.timetuple())
        order_details['status'] = order.status

        orders.append(order_details)

    orders = sorted(orders, key=lambda k: k['order_id'], reverse=True)

    RESULT_JSON['customer_id'] = customer_id
    RESULT_JSON['customer_name'] = full_name
    RESULT_JSON['customer_email'] = email
    RESULT_JSON['orders'] = orders
    RESULT_JSON['status'] = 200

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


def getCustomerPreferences(request):
    data = json.loads(request.body)
    errors = []
    RESULT_JSON = {}
    customer_details = {}

    customer_id = int(data['customer_id'])

    try:
        customer = Customer.objects.get(id=customer_id)

        customer_preferences = Preferences.objects.get(customer_id=customer_id)
        flavors_set = customer_preferences.flavor.all()
        flavors = []
        for flavor in flavors_set:
            flavors.append(flavor.name)

        customer_details['customer_name'] = customer.first_name.capitalize() + ' ' + customer.last_name.capitalize()
        customer_details['first_name'] = customer.first_name
        customer_details['last_name'] = customer.last_name
        customer_details['customer_email'] = customer.user.email
        customer_details['address_first'] = customer.line1
        customer_details['address_second'] = customer.line2
        customer_details['postal_code'] = customer.postcode
        customer_details['phone'] = customer.phone
        customer_details['credits'] = customer.amount
        customer_details['vouchers'] = customer.get_vouchers_name()
        customer_details['coffee_id'] = customer_preferences.coffee_id
        customer_details['coffee'] = customer_preferences.coffee.name
        customer_details['flavor'] = flavors
        customer_details['brew_method'] = customer_preferences.brew.name
        customer_details['packaging_method'] = customer_preferences.package
        customer_details['decaffeinated'] = customer_preferences.decaf
        customer_details['different'] = customer_preferences.different
        customer_details['different_pods'] = customer_preferences.different_pods
        customer_details['cups'] = customer_preferences.cups
        customer_details['intense'] = customer_preferences.intense
        customer_details['interval'] = customer_preferences.interval
        customer_details['interval_pods'] = customer_preferences.interval_pods

        shipping_date = datetime.datetime.now() + datetime.timedelta(days=1)

        customer_details['shipping_date'] = time.mktime(shipping_date.timetuple())

        RESULT_JSON['status'] = 200
        RESULT_JSON['customer_details'] = customer_details

    except ObjectDoesNotExist as e:
        errors.append(str(e))
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = errors
        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


def addOrder(request):
    errors = []
    RESULT_JSON = {}
    data = json.loads(request.body)

    customer_id = int(data['customer_id'])
    coffee_id = int(data['coffee_id'])
    recurrent = data['recurrent']

    try:
        customer = Customer.objects.get(id=customer_id)
        coffee = CoffeeType.objects.get(id=coffee_id)
    except ObjectDoesNotExist as e:
        errors.append(str(e))

    if errors:
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = errors
        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    customer_preferences = Preferences.objects.get(customer_id=customer_id)
    brew_method = BrewMethod.objects.get(name_en=data['brew_method'])
    packaging_method = data['packaging_method']
    shipping_date = datetime.datetime.strptime(data['shipping_date'], "%d-%m-%Y")

    if shipping_date.date() < datetime.date.today():
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = 'Shipping date cannot be a past date'
        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    shipping_date = shipping_date.replace(hour=12, minute=0, second=0, microsecond=0)

    try:
        if brew_method.name == 'Nespresso':
            order = Order(
                customer = customer,
                coffee = coffee,
                date = datetime.datetime.now(),
                shipping_date = shipping_date,
                amount = coffee.amount,
                interval = customer_preferences.interval_pods,
                recurrent = recurrent,
                status = Order.ACTIVE,
                brew = brew_method,
                package=packaging_method,
                different = customer_preferences.different_pods,
            )

        else:
            order = Order(
                customer=customer,
                coffee=coffee,
                date=datetime.datetime.now(),
                shipping_date=shipping_date,
                amount=coffee.amount,
                interval=customer_preferences.interval,
                recurrent=recurrent,
                status=Order.ACTIVE,
                brew=brew_method,
                package=packaging_method,
                different=customer_preferences.different,
            )

        order.save()

    except Exception as e:
        errors.append(str(e))
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = errors
        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


    RESULT_JSON['status'] = 200
    RESULT_JSON['message'] = 'Order has been successfully created'

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


def resendOrder(request):
    errors = []
    RESULT_JSON = {}
    data = json.loads(request.body)

    order_id = int(data['order_id'])

    try:
        order = Order.objects.get(id=order_id)
    except Exception as e:
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = 'No order was found matching the given ID'

        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    if order.status != 'SH':
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = 'You may only resend shipped orders'

        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    customer = order.customer
    coffee = order.coffee

    try:
        new_order = Order(
                customer=customer,
                coffee=coffee,
                date=datetime.datetime.now(),
                shipping_date=getNextShippingDate(order.shipping_date, None), #shipping date to be tomorrow's date
                amount=0,
                interval=order.interval,
                recurrent=False,
                status=Order.ACTIVE,
                brew=order.brew,
                package=order.package,
                different=order.different,
                resent=True
            )
        new_order.save()
        order.status = Order.CANCELED
        order.save()

        send_replacement_email(request, order)
    except Exception as e:
        errors.append(str(e))
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = errors
        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    RESULT_JSON['status'] = 200
    RESULT_JSON['message'] = 'Order has been successfully re-created and is ready for processing'

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


def getOrderDetails(request):
    RESULT_JSON = {}
    data = json.loads(request.body)

    order_id = int(data['order_id'])

    try:
        order = Order.objects.get(id=order_id)
    except Exception as e:
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = 'No order was found matching the given ID'

        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    settings_time_zone = pytz.timezone(settings.TIME_ZONE)

    created_date = order.date
    created_date = created_date.astimezone(settings_time_zone)

    shipping_date = order.shipping_date
    shipping_date = shipping_date.astimezone(settings_time_zone)

    order_details = {}
    order_details['customer_id'] = order.customer_id
    order_details['customer_name'] = order.customer.first_name.capitalize() + ' ' + order.customer.last_name.capitalize()
    order_details['customer_email'] = order.customer.user.email
    order_details['coffee'] = order.coffee.name
    order_details['coffee_id'] = order.coffee_id
    order_details['brew_method'] = order.brew.name
    order_details['packaging_method'] = order.package
    order_details['created_date'] = time.mktime(created_date.timetuple())
    order_details['shipping_date'] = time.mktime(shipping_date.timetuple())
    order_details['status'] = order.status
    order_details['custom_price'] = order.custom_price

    RESULT_JSON['status'] = 200
    RESULT_JSON['order_details'] = order_details

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


def editOrder(request):
    RESULT_JSON = {}
    data = json.loads(request.body)
    errors = []

    order_id = int(data['order_id'])
    custom_price = data['custom_price']

    if custom_price:
        price = data['price']
        if price is not None:
            price = float(price)
        else:
            RESULT_JSON['status'] = 500
            RESULT_JSON['error_message'] = 'Please input a price'

            return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    try:
        order = Order.objects.get(id=order_id)
    except Exception as e:
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = 'No order was found matching the given ID'

        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    try:
        coffee = CoffeeType.objects.get(id=int(data['coffee_id']))
    except Exception as e:
        coffee = None

    try:
        brew_method = BrewMethod.objects.get(name_en=data['brew_method'])
    except Exception as e:
        brew_method = None

    packaging_method = data['packaging_method']
    shipping_date = datetime.datetime.strptime(data['shipping_date'], "%d-%m-%Y").date()

    if shipping_date < datetime.date.today():
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = 'Shipping date cannot be a past date'
        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    try:
        order.coffee = coffee
        order.brew = brew_method
        order.package = packaging_method
        order.shipping_date = shipping_date
        order.custom_price = custom_price
        if custom_price:
            order.amount = price
        order.save()
    except Exception as e:
        errors.append(str(e))
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = errors
        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    RESULT_JSON['status'] = 200
    RESULT_JSON['message'] = 'Order has been successfully edited'

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


def cancelOrder(request):
    RESULT_JSON = {}
    data = json.loads(request.body)

    order_id = int(data['order_id'])

    try:
        order = Order.objects.get(id=order_id)
    except Exception as e:
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = 'No order was found matching the given ID'

        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    if order.status == Order.ACTIVE:
        order.status = Order.CANCELED
        order.save()
    else:
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = 'You may only cancel orders that are ACTIVE'

        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    RESULT_JSON['status'] = 200
    RESULT_JSON['message'] = 'Order has been successfully cancelled'

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

#
def getOrderPrice(request):
    RESULT_JSON = {}
    data = json.loads(request.body)
    order = None

    try:
        coffee_id = int(data['coffee_id'])
        coffee = CoffeeType.objects.get(id=coffee_id)
    except Exception as e:
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = 'Please input a coffee'

        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    try:
        order_id = int(data['order_id'])
        order = Order.objects.get(id=order_id)
    except Exception as e:
        #for adding of new orders where no order ID will be given
        price = coffee.amount
        RESULT_JSON['status'] = 200
        RESULT_JSON['price'] = format(float(price), '.2f')

        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    custom_price = order.custom_price

    if custom_price:
        price = order.amount
    else:
        voucher = order.voucher
        if voucher:
            discount_1 = voucher.discount
            discount_2 = voucher.discount2
            price = coffee.amount -  coffee.amount * discount_1 / 100 - discount_2
        else:
            price = coffee.amount

    RESULT_JSON['status'] = 200
    RESULT_JSON['price'] = format(float(price), '.2f')

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


def editCustomerPreferences(request):
    RESULT_JSON = {}
    errors = []
    data = json.loads(request.body)

    customer_id = int(data['customer_id'])
    flavor_name_arr = data['flavor']
    voucher_name_arr = data['vouchers']
    flavors = []
    vouchers = []

    try:
        customer = Customer.objects.get(id=customer_id)
        customer_preferences = Preferences.objects.get(customer_id=customer_id)
        user = MyUser.objects.get(id=customer.user_id)

        if flavor_name_arr:
            for flavor_name in flavor_name_arr:
                flavor = Flavor.objects.get(name=flavor_name)
                flavors.append(flavor)
            customer_preferences.flavor = flavors

        if voucher_name_arr:
            for voucher_name in voucher_name_arr:
                voucher = Voucher.objects.get(name=voucher_name)
                vouchers.append(voucher)
            customer.vouchers = vouchers

        customer.first_name = data['first_name']
        customer.last_name = data['last_name']
        user.email = data['customer_email']
        customer.line1 = data['address_first']
        customer.line2 = data['address_second']
        customer.postcode = data['postal_code']
        customer.phone = data['phone']
        customer.amount = int(data['credits'])
        customer_preferences.coffee = CoffeeType.objects.get(id=int(data['coffee_id']))
        customer_preferences.brew = BrewMethod.objects.get(name_en=data['brew_method'])
        customer_preferences.package = data['packaging_method']
        customer_preferences.decaf = data['decaffeinated']
        customer_preferences.different = data['different']
        customer_preferences.different_pods = data['different_pods']
        customer_preferences.cups = int(data['cups'])
        customer_preferences.intense = int(data['intense'])
        customer_preferences.interval = int(data['interval'])
        customer_preferences.interval_pods = int(data['interval_pods'])

        customer.save()
        user.save()
        customer_preferences.save()

        RESULT_JSON['status'] = 200
        RESULT_JSON['message'] = 'Edit Successful'

        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    except Exception as e:
        errors.append(str(e))
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = errors
        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


def getFlavors(request):
    RESULT_JSON = {}
    flavors = []

    flavors_set = Flavor.objects.all()
    for flavor in flavors_set:
        flavor_details = {}
        flavor_details['flavor_id'] = flavor.id
        flavor_details['flavor_name'] = flavor.name
        flavors.append(flavor_details)

    RESULT_JSON['status'] = 200
    RESULT_JSON['flavors'] = flavors

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


def getVouchers(request):
    RESULT_JSON = {}
    vouchers = []

    vouchers_set = Voucher.objects.filter(mode=True)
    for voucher in vouchers_set:
        voucher_details = {}
        voucher_details['voucher_id'] = voucher.id
        voucher_details['voucher_name'] = voucher.name
        voucher_details['mode'] = voucher.mode
        voucher_details['discount_percentage'] = voucher.discount
        voucher_details['discount_dollars'] = voucher.discount2
        voucher_details['count'] = voucher.count
        vouchers.append(voucher_details)

    RESULT_JSON['status'] = 200
    RESULT_JSON['vouchers'] = vouchers

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')
