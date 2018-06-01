# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
from datetime import datetime, timedelta
from io import BytesIO
from itertools import chain

from PyPDF2 import PdfFileReader, PdfFileWriter

from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.utils import timezone

from coffees.models import CoffeeType

from customers.models import Customer, GearOrder, Order, Preferences


ELEMENT_POSITION = {
    'name': {'left': (25, 70), 'right': ()},
    'roasted_on': {'left': (57, 50), 'right': ()},
    'ground_on': {'left': (150, 50), 'right': ()},
    'package': {
        'Wholebeans': {'left': (138, 14), 'right': ()},
        'Espresso': {'left': (60, 28), 'right': ()},
        'Aeropress': {'left': (102, 28), 'right': ()},
        'French press': {'left': (151, 28), 'right': ()},
        'Cold Brew': {'left': (15, 14), 'right': ()},
        'Stove top': {'left': (60, 14), 'right': ()},
        'Drip': {'left': (102, 14), 'right': ()},
    },
    'barcode': {'left': (220, 5), 'right': ()},
}


AMATIC_BOLD = TTFont(
    'Amatic-Bold', os.path.join(settings.STATIC_PATH,
                                'fonts/amatic/Amatic-Bold.ttf'))
AVENIRNEXT = TTFont(
    'AvenirNext', os.path.join(settings.STATIC_PATH,
                               'fonts/avenir/AvenirNext-DemiBold_gdi.ttf'))
DROIDSANSFALLBACK = TTFont(
    'DroidSansFallback',
    os.path.join(settings.STATIC_PATH, 'fonts/free/DroidSansFallback.ttf'))

HOOKCOFFEECLUB = TTFont(
    'HookCoffee Club',
    os.path.join(settings.STATIC_PATH, 'fonts/HookCoffee Club.ttf'))

ARBORIA_BOOK = TTFont(
    'ArboriaBook', os.path.join(settings.STATIC_PATH,
                                'fonts/arboria/Arboria-Book-fixed.ttf'))


def _create_barcode(order_id):
    """Create and return a drawing with a barcode (Code128)."""
    return createBarcodeDrawing(codeName='Code128', value='@%s' % order_id)


def _create_qr(order_id, size=23):
    """Create and return a drawing with a QR code."""
    link = '{host}{path}'.format(
        host='https://hookcoffee.com.sg',
        path=reverse('qr_social', kwargs={'order_id': order_id}))
    return createBarcodeDrawing(
        codeName='QR', value=link,
        barWidth=size * mm, barHeight=size * mm)


def generate_qr_coffee(coffee):
    pdfmetrics.registerFont(AMATIC_BOLD)

    buffer = BytesIO()

    width, height = (500, 300)
    c = canvas.Canvas(buffer, pagesize=(width, height))
    c.setLineWidth(.3)
    c.setFont('Amatic-Bold', 36)

    w = width / 2.0
    c.drawCentredString(w, 160, '%s' % coffee.name)

    # prefix '0' used for we can differentiate between OrderID and CoffeeTypeID in the DB
    # see qr_social() in .views
    barcode = _create_qr('0%d' % coffee.id)
    barcode.drawOn(c, 217, 10)

    c.showPage()
    c.save()

    label = BytesIO(buffer.getvalue())
    buffer.close()

    return label


def generate_qr_all_coffees():
    coffees_all = CoffeeType.objects.all()
    output = PdfFileWriter()

    for coffee in coffees_all:
        page_buffer = generate_qr_coffee(coffee)
        page = PdfFileReader(page_buffer).getPage(0)
        output.addPage(page)

    pages = BytesIO()
    output.write(pages)

    return pages


def generate_common_product_label(order):
    pdfmetrics.registerFont(AMATIC_BOLD)
    pdfmetrics.registerFont(DROIDSANSFALLBACK)

    buffer = BytesIO()

    width, height = (500, 300)
    c = canvas.Canvas(buffer, pagesize=(width, height))
    c.setLineWidth(.3)

    recipient = order.shipping_address['recipient_name']
    if _is_ascii_str(recipient):
        font_for_name = 'Amatic-Bold'
    else:
        font_for_name = 'DroidSansFallback'
    c.setFont(font_for_name, 36)

    w = width / 2.0
    c.drawCentredString(w, 250, recipient)

    if isinstance(order, GearOrder):
        product_name = order.gear.name
        extra_name = ''
        barcode = _create_qr('G%s' % order.pk)
    else:
        product_name = order.coffee.name
        extra_name = 'SHOTPODS'
        barcode = _create_qr(order.pk)

    c.drawCentredString(w, 160, product_name)
    c.drawCentredString(w, 115, extra_name)
    barcode.drawOn(c, 217, 10)

    c.showPage()
    c.save()

    label = BytesIO(buffer.getvalue())
    buffer.close()

    return label


def generate_product_label(order):
    if order.coffee.roasted_on:
        roasted_on = order.coffee.roasted_on
    else:
        roasted_on = timezone.now() + timedelta(days=-3)

    package = order.package
    brew = order.brew.name

    side = 'left' if order.coffee.label_position == 1 else 'right'

    roasted_on = datetime.strftime(roasted_on, '%d / %b / %y')
    ground_on = ('' if package == Preferences.WHOLEBEANS else
                   datetime.strftime(order.shipping_date, '%d / %b / %y'))

    if package == Preferences.DRIP_BAGS:
        template_src = os.path.join(settings.MEDIA_ROOT, str(order.coffee.label_drip))
    else:
        template_src = os.path.join(settings.MEDIA_ROOT, str(order.coffee.label))

    pdfmetrics.registerFont(AMATIC_BOLD)
    pdfmetrics.registerFont(DROIDSANSFALLBACK)
    # pdfmetrics.registerFont(AVENIRNEXT)

    buffer = BytesIO()

    c = canvas.Canvas(buffer)

    c.setLineWidth(.3)

    recipient = order.shipping_address['recipient_name']
    if _is_ascii_str(recipient):
        recipient = '{:^35}'.format(recipient)
        font_for_name = 'Amatic-Bold'
    else:
        recipient = '{:^15}'.format(recipient)
        font_for_name = 'DroidSansFallback'

    c.setFont(font_for_name, 16)
    x, y = ELEMENT_POSITION['name'][side]
    c.drawString(x, y, recipient)

    c.setFont('Amatic-Bold', 14)
    x, y = ELEMENT_POSITION['roasted_on'][side]
    c.drawString(x, y, roasted_on)

    x, y = ELEMENT_POSITION['ground_on'][side]
    c.drawString(x, y, ground_on)

    c.setFont('Helvetica', 16)
    if package == Preferences.GRINDED:
        brew_pos = ELEMENT_POSITION['package'].get(brew)
        if brew_pos:
            brew_pos = brew_pos[side]
            c.drawString(brew_pos[0], brew_pos[1], '✔')
    elif package == Preferences.WHOLEBEANS:
        brew_pos = ELEMENT_POSITION['package']['Wholebeans'][side]
        c.drawString(brew_pos[0], brew_pos[1], '✔')

    barcode_pos = ELEMENT_POSITION['barcode'][side]
    barcode = _create_qr(order.pk)
    barcode.drawOn(c, *barcode_pos)

    c.showPage()
    c.save()

    page = PdfFileReader(template_src).getPage(0)
    overlay = PdfFileReader(buffer).getPage(0)
    page.mergePage(overlay)

    label = BytesIO()

    output = PdfFileWriter()
    output.addPage(page)
    output.write(label)

    return label


def generate_all_product_labels(special=False, part_labels=0, per_file=10000, customer=None):
    ctz = timezone.get_current_timezone()
    now = ctz.normalize(timezone.now())
    day = now.isoweekday()

    # today = now.replace(
    #     hour=12, minute=0, second=0, microsecond=0)
    tomorrow = now.replace(
        hour=12, minute=0, second=0, microsecond=0) + timedelta(days=1)
    two_days_later = now.replace(
        hour=12, minute=0, second=0, microsecond=0) + timedelta(days=2)
    three_days_later = now.replace(
        hour=12, minute=0, second=0, microsecond=0) + timedelta(days=3)

    my_shipping_date = tomorrow
    # Friday
    if day == 5:
        my_shipping_date = three_days_later

    # Saturday
    elif day == 6:
        my_shipping_date = two_days_later

    if not customer:
        orders = Order.objects.filter(
                shipping_date__lte=my_shipping_date,
                status__in=[Order.ACTIVE, Order.PAUSED, Order.ERROR])\
            .order_by('coffee', 'brew', 'package')
    else:
        orders = Order.objects.filter(
                customer=customer,
                shipping_date__lte=my_shipping_date,
                status__in=[Order.ACTIVE, Order.PAUSED, Order.ERROR])\
            .order_by('coffee', 'brew', 'package')

    orders_gear = GearOrder.objects.filter(
        shipping_date__lte=my_shipping_date,
        status__in=[Order.ACTIVE, Order.PAUSED, Order.ERROR])\
        .order_by('id')

    if special:
        orders = orders.filter(
            coffee__label__exact='', coffee__label_drip__exact='')
        orders = list(chain(orders, orders_gear))
    else:
        orders = orders.exclude(
            coffee__label__exact='', coffee__label_drip__exact='')
        if part_labels:
            all_orders = Paginator(orders, per_file)
            orders = all_orders.page(part_labels)

    output = PdfFileWriter()

    pdfmetrics.registerFont(AMATIC_BOLD)
    # pdfmetrics.registerFont(AVENIRNEXT)

    for order in orders:
        if special:
            label_buffer = generate_common_product_label(order)
        else:
            label_buffer = generate_product_label(order)

        page = PdfFileReader(label_buffer).getPage(0)
        output.addPage(page)

    labels = BytesIO()
    output.write(labels)

    return labels


def generate_address_label(order):
    try:
        customer = order.customer
    except AttributeError:  # For RedemItem, that haven't relation to customer
        customer = Customer.objects.get(user=order.user)

    buffer = BytesIO()

    width, height = (1080, 470)
    c = canvas.Canvas(buffer, pagesize=(width, height))
    c.setLineWidth(.3)

    pdfmetrics.registerFont(DROIDSANSFALLBACK)  # for non Ascii
    pdfmetrics.registerFont(ARBORIA_BOOK)

    w = width / 2.0

    if isinstance(order, (Order, GearOrder)):
        address = order.shipping_address
        recipient = address['recipient_name']
        line1 = address['line1']
        line2 = address['line2']
        country_name = address['country'].name
        postcode = address['postcode']
        order.update_shipped_to(address)
    else:
        recipient = customer.get_full_name()
        line1 = customer.line1
        line2 = customer.line2
        country_name = customer.country.name
        postcode = customer.postcode

    c.setFont('ArboriaBook', 48)
    c.drawString(50, 400, 'TAKE ME TO:')
    if _is_ascii_str(recipient):
        font, font_size = ('ArboriaBook', 58)
    else:
        font, font_size = ('DroidSansFallback', 48)
    c.setFont(font, font_size)
    c.drawCentredString(w, 310, recipient)
    c.drawCentredString(w, 240, line1)
    c.drawCentredString(w, 170, line2)
    c.drawCentredString(w, 100, '{}, {}'.format(country_name, postcode))

    c.showPage()
    c.save()

    label = BytesIO(buffer.getvalue())
    buffer.close()

    return label


def generate_all_address_labels():
    ctz = timezone.get_current_timezone()
    now = ctz.normalize(timezone.now())
    day = now.isoweekday()

    # today = now.replace(
    #     hour=12, minute=0, second=0, microsecond=0)
    tomorrow = now.replace(
        hour=12, minute=0, second=0, microsecond=0) + timedelta(days=1)
    two_days_later = now.replace(
        hour=12, minute=0, second=0, microsecond=0) + timedelta(days=2)
    three_days_later = now.replace(
        hour=12, minute=0, second=0, microsecond=0) + timedelta(days=3)

    my_shipping_date = tomorrow
    # Friday
    if day == 5:
        my_shipping_date = three_days_later

    # Saturday
    elif day == 6:
        my_shipping_date = two_days_later

    orders = Order.objects.filter(
        shipping_date__lte=my_shipping_date,
        status__in=[Order.ACTIVE, Order.PAUSED, Order.ERROR])\
        .order_by('coffee', 'brew', 'package')

    gear_orders = GearOrder.objects.filter(
        shipping_date__lte=my_shipping_date,
        status__in=[Order.ACTIVE, Order.PAUSED, Order.ERROR])\
        .order_by('id')

    orders = list(chain(orders, gear_orders))

    output = PdfFileWriter()

    for order in orders:
        label_buffer = generate_address_label(order)
        page = PdfFileReader(label_buffer).getPage(0)
        output.addPage(page)

    labels = BytesIO()
    output.write(labels)

    return labels


def _is_ascii_str(string):
    try:
        string.decode('ascii')
    except UnicodeError:
        return False
    else:
        return True
