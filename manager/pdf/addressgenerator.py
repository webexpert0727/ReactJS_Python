# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import hashlib
import os
import tempfile
import base64
from StringIO import StringIO
from wsgiref.util import FileWrapper

from PyPDF2 import PdfFileReader, PdfFileWriter

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from django.conf import settings
from django.http import HttpResponse
from django.http import StreamingHttpResponse

from customers.models import Customer, GearOrder, Order

from loyale.models import RedemItem

from ..utils import getOrderIdAndHashFromFilePath


DROIDSANSFALLBACK = TTFont(
    'DroidSansFallback',
    os.path.join(settings.STATIC_PATH, 'fonts/free/DroidSansFallback.ttf'))

HOOKCOFFEECLUB = TTFont(
    'HookCoffee Club',
    os.path.join(settings.STATIC_PATH, 'fonts/HookCoffee Club.ttf'))

ARBORIA_BOOK = TTFont(
    'ArboriaBook',
    os.path.join(settings.STATIC_PATH, 'fonts/arboria/Arboria-Book-fixed.ttf'))


def generate_address(order, customer=None):
    if order:
        customer = order.customer

    buffer = StringIO()

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

    overlay = PdfFileReader(buffer).getPage(0)
    return overlay


def generate_roadbull(order):
    content = order.roadbull.all()[0].label_pdf
    decoded_content = base64.b64decode(content)

    f = StringIO(decoded_content)
    pdf = PdfFileReader(f, strict=False)
    page = pdf.getPage(0)

    return page


def print_address_by_customer(customer_id):
    customer = Customer.objects.get(id=customer_id)

    filename = 'cus_%s_address.pdf' % customer_id
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename

    page = generate_address(None, customer)
    output = PdfFileWriter()
    output.addPage(page)
    output.write(response)
    return response


def print_addresses(orders):
    temp = tempfile.TemporaryFile()
    output = PdfFileWriter()

    for order_id, order_type in orders:
        if order_type == 'GEAR':
            model = GearOrder
        elif order_type == 'REDEM':
            model = RedemItem
        else:
            model = Order

        order = model.objects.get(id=order_id)
        if isinstance(order, RedemItem):
            page = generate_address(None, order.user.customer)
        else:
            if isinstance(order, GearOrder) and order.roadbull.all():
                page = generate_roadbull(order)
            else:
                page = generate_address(order)

        output.addPage(page)

    output.write(temp)

    chunk_size = 8192
    wrapper = FileWrapper(temp, chunk_size)

    if len(orders) == 1:
        order_id, _ = orders[0]
        filename = '%s_address.pdf' % order_id
    else:
        filename = 'all_addresses.pdf'
    response = StreamingHttpResponse(wrapper, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    response['Content-Length'] = temp.tell()
    temp.seek(0)
    return response


# def print_all_addresses(ids):
#     try:
#         temp = tempfile.TemporaryFile()
#         output = PdfFileWriter()
#         pageFilesTuples = []
#         try:
#             allPages = getAddressQueue()
#             pageFilesTuples = filter(lambda page : int(page[0][0]) in ids, allPages)
#             # for those addresses that exist, we simply get the cached version
#             for pageFileTup in pageFilesTuples:
#                 order = Order.objects.get(id=int(pageFileTup[0][0]))
#                 addr_hash = hashlib.md5(order.customer.get_full_address()).hexdigest()
#                 if addr_hash == pageFileTup[0][1]:
#                     with file(pageFileTup[1], 'rb') as f:
#                         pageFile = StringIO(f.read())
#                     page = PdfFileReader(pageFile).getPage(0)
#                     output.addPage(page)
#                 else:
#                     page = generate_address(Order.objects.get(id=int(pageFileTup[0][0])))
#                     output.addPage(page)
#         except Exception as e:
#             print e
#             print 'Error finding directory for generated addresses'
#         #failsafe for non-existing addresses
#         for id in ids:
#             if id not in [int(pageFileTuple[0][0]) for pageFileTuple in pageFilesTuples]:
#                 page = generate_address(Order.objects.get(id=id))
#                 output.addPage(page)
#         output.write(temp)
#         chunk_size = 8192
#         wrapper = FileWrapper(temp, chunk_size)
#         response = StreamingHttpResponse(wrapper, content_type='application/pdf')
#         response['Content-Disposition'] = 'attachment; filename=all_addresses.pdf'
#         response['Content-Length'] = temp.tell()
#         temp.seek(0)
#         return response


def getAddressQueue():
    # returns a list of tuples (id, file) of all objects on filesystem at STATIC_PATH/labels/<order_id>.pdf
    address_path = settings.ADDRESS_PATH
    files_in_dir = os.listdir(address_path)

    id_and_files = map(lambda file: (getOrderIdAndHashFromFilePath(file), address_path + file), files_in_dir)
    return id_and_files


def _is_ascii_str(string):
    try:
        string.decode('ascii')
    except UnicodeError:
        return False
    else:
        return True
