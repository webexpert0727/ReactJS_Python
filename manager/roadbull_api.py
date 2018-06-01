import json
import logging
import requests

from django.utils import timezone
from datetime import datetime, timedelta
from django.conf import settings
from giveback_project.helpers import get_shipping_date

from manager.models import RoadbullOrder


logger = logging.getLogger('giveback_project.' + __name__)
CTZ = timezone.get_current_timezone()

def main(order):
    booking_json = order_booking(order)
    if booking_json.get('Code') == 0:
        order_number = booking_json.get('OrderNumber')
        consignment_number = booking_json.get('ConsignmentNumber')
        tracking_number = booking_json.get('TrackingNumber')


        label_json = get_label(consignment_number)
        if label_json.get('code') == 200:
            label_pdf = label_json.get('data').get('label_pdf')
            bar_code_url = label_json.get('data').get('bar_code_url')
            qr_code_url = label_json.get('data').get('qr_code_url')

            RoadbullOrder.objects.create(gear_order=order,
                order_number=order_number,
                consignment_number=consignment_number,
                tracking_number=tracking_number,
                bar_code_url=bar_code_url,
                qr_code_url=qr_code_url,
                label_pdf=label_pdf)

            return {
                'Code': 0,
                'bar_code_url': bar_code_url,
                'qr_code_url': qr_code_url,
                'label_pdf': label_pdf,
                'tracking_number': tracking_number,
            }

        else:
            return booking_json

    else:
        return booking_json


def login():
    """This API allows user to login to Roadbull System.

    This will return you with a token and henceforth for all further request
    you should pass it in the request header.
    """

    url = 'http://{server}/api/accounts/login'.format(server=settings.ROADBULL_SERVER)
    data = {
        "UserName": settings.ROADBULL_USERNAME,
        "Password": settings.ROADBULL_PASSWORD,
        "RememberMe": True,
    }

    try:
        response = requests.post(url, json=data)
    except Exception as e:
        logger.error("Roadbull login failed: {}".format(e))
    else:
        if response.status_code == 200:
            return "Bearer {}".format(response.json().get('Token'))

    return None


def get_product_type():
    """This API allows user to get the Product Type information."""

    url = "http://{server}/api/orders/producttypes".format(server=settings.ROADBULL_SERVER)

    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return {
        'Code': response.status_code
        }

def get_parcel_size(product_type_id):
    """This API allows user to get the parcel size information.

    Authentication is required for this API.
    """

    url = "http://{server}/api/orders/sizes".format(server=settings.ROADBULL_SERVER)
    data = {
        'ProductTypeId': product_type_id
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    return {
        'Code': response.status_code
        }


def get_services(product_type_id, size_id):
    """This API allows user to get the Services information.

    Authentication is required for this API.
    """

    url = "http://{server}/api/orders/services".format(server=settings.ROADBULL_SERVER)
    data = {
        'ProductTypeId': product_type_id,
        "SizeId ": size_id
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    return {
        'Code': response.status_code
        }


def get_time_options(service_id):
    """This API allows user to get the Time Options information.

    Authentication is required for this API.
    """

    url = "http://{server}/api/orders/timeoptions/{service_id}".format(server=settings.ROADBULL_SERVER, service_id=service_id)

    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return {
        'Code': response.status_code
        }


def order_booking(order, product_type_id=settings.ROADBULL_PRODUCTTYPEID):
    """This API allows user to book the Single Order.

    Authentication is required for this API.
    Authorization token got from the login API method should be passed in the request header.
    """

    url = "http://{server}/api/orders/book".format(server=settings.ROADBULL_SERVER)
    size_id = settings.ROADBULL_SMALL
    if order.gear.name == 'The Hook Coffee Advent Calendar (x2)':
        size_id = settings.ROADBULL_MEDIUM

    pickup_date, delivery_date = get_pickup_delivery_dates()
    pickup_date = _format_date(pickup_date)
    delivery_date = _format_date(delivery_date)

    service_id = settings.ROADBULL_SERVICEID
    pickup_time_slot_id = 26
    delivery_time_slot_id = 5
    logger.debug("Book Roadbull for order id={}, pickup_date={}, delivery_date={}".format(
        order.id, pickup_date, delivery_date))

    data = {
        "FromName": settings.ROADBULL_FROMNAME,
        "FromZipCode": settings.ROADBULL_FROMZIPCODE,
        "FromAddress": settings.ROADBULL_FROMADDRESS,
        "FromMobilePhone": settings.ROADBULL_FROMMOBILEPHONE,

        "ToName": order.address.recipient_name if order.address else order.customer.get_full_name(),
        "ToZipCode": order.address.postcode if order.address else order.customer.postcode,
        "ToAddress": order.address.get_address() if order.address else order.customer.get_full_address(),
        "ToMobilePhone": order.customer.phone,

        "ServiceId": service_id,
        "ProductTypeId": product_type_id,
        "SizeId": size_id,
        "PickupTimeSlotId": pickup_time_slot_id,
        "PickupDate": pickup_date,
        "DeliveryTimeSlotId": delivery_time_slot_id,
        "DeliveryDate": delivery_date,

        "OrderNumber": order.id,
        "SenderEmail": settings.ROADBULL_SENDEREMAIL,

        "Weight": str(order.gear.weight/1000.) # in kilograms
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    return {
        'Code': response.status_code
        }

def get_label(consignment_number):
    """This API allows user to get the Order Label information.

    Authentication is required for this API.
    Authorization token got from the login API method should be passed in the request header.
    """

    url = "http://{server}/api/orders/label/{consignmentNumber}".format(server=settings.ROADBULL_SERVER, consignmentNumber=consignment_number)

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return {
        'Code': response.status_code
        }

def _format_date(date):
    return datetime.strftime(date, "%d/%m/%Y")

def get_pickup_delivery_dates():
    now = CTZ.normalize(timezone.now())
    day = now.isoweekday()
    today = now.replace(hour=12, minute=0, second=0, microsecond=0)
    noon = now.replace(hour=11, minute=0, second=0, microsecond=0)
    morning = True if now < noon else False

    if morning:
        if day in range(1, 5):
            return today, today + timedelta(days=1)
        if day == 5:
            return today, today + timedelta(days=3)
        if day == 6:
            return today, today + timedelta(days=2)
        if day == 7:
            return today, today + timedelta(days=1)
    else:
        if day in range(1, 4):
            return today + timedelta(days=1), today + timedelta(days=2)
        if day ==4:
            return today + timedelta(days=1), today + timedelta(days=4)
        if day ==5:
            return today + timedelta(days=3), today + timedelta(days=4)
        if day ==6:
            return today + timedelta(days=2), today + timedelta(days=3)
        if day ==7:
            return today + timedelta(days=1), today + timedelta(days=2)


headers = {
    'authorization': login()
}
