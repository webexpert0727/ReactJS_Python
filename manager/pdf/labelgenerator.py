# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import hashlib
import os
import tempfile
from StringIO import StringIO
from datetime import datetime, timedelta
from wsgiref.util import FileWrapper

from PyPDF2 import PdfFileWriter, PdfFileReader

from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import StreamingHttpResponse
from django.utils import timezone

from coffees.models import CoffeeType

from customers.models import GearOrder, Order, Preferences

from loyale.models import RedemItem

from ..utils import getOrderIdAndHashFromFilePath, hasOwnLabel


ELEMENT_POSITION = {
    'name': {'left': (25, 70), 'right': ()},
    'roasted_on': {'left': (57, 50), 'right': ()},
    'ground_on': {'left': (150, 50), 'right': ()},
    'ground_for': {'left': (125, 32), 'right': ()},
    'package': {'left': (117, 15), 'right': ()},
    'barcode': {'left': (220, 5), 'right': ()},
}

AMATIC_BOLD = TTFont(
    'Amatic-Bold', os.path.join(settings.STATIC_PATH,
                                'fonts/amatic/Amatic-Bold.ttf'))
OPEN_SANS = TTFont(
    'Open-Sans', os.path.join(settings.STATIC_PATH,
                              'fonts/open-sans/OpenSans-Light.ttf'))
HOOKCOFFEE_CLUB = TTFont(
    'HookCoffeeClub', os.path.join(settings.STATIC_PATH,
                                   'fonts/HookCoffee Club.ttf'))


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


def generate_label(order_id, coffee_id=None):
    pdfmetrics.registerFont(AMATIC_BOLD)
    pdfmetrics.registerFont(HOOKCOFFEE_CLUB)

    order = Order.objects.get(id=order_id)
    # coffee_id for Discovery Pack:
    coffee = (CoffeeType.objects.get(id=coffee_id) if coffee_id else
              order.coffee)
    package = order.package
    brew = order.brew.name

    recipient = order.shipping_address['recipient_name']
    name = '{:^35}'.format(recipient)
    if coffee.roasted_on:
        roasted_on = coffee.roasted_on
    else:
        roasted_on = timezone.now() + timedelta(days=-3)

    side = 'left' if coffee.label_position == 1 else 'right'

    roasted_on = datetime.strftime(roasted_on, '%d / %b / %y')
    ground_on = ('' if package == Preferences.WHOLEBEANS else
                 datetime.strftime(order.shipping_date, '%d / %b / %y'))

    if not coffee.hasLabel:
        raise ValueError(coffee.id, coffee)

    if package == Preferences.DRIP_BAGS:
        template_src = os.path.join(settings.MEDIA_ROOT, str(coffee.label_drip))
    else:
        template_src = os.path.join(settings.MEDIA_ROOT, str(coffee.label))

    buffer = StringIO()

    c = canvas.Canvas(buffer)

    c.setLineWidth(.3)

    c.setFont('Amatic-Bold', 16)
    x, y = ELEMENT_POSITION['name'][side]
    c.drawString(x, y, name)

    c.setFont('Amatic-Bold', 14)
    x, y = ELEMENT_POSITION['roasted_on'][side]
    c.drawString(x, y, roasted_on)

    x, y = ELEMENT_POSITION['ground_on'][side]
    c.drawString(x, y, ground_on)

    if package != Preferences.DRIP_BAGS:
        if package == Preferences.WHOLEBEANS:
            prefix = ''
            ground_for = 'Whole beans'
        elif package == Preferences.GRINDED:
            prefix = 'ground for'
            if brew == 'None':
                prefix = ''
                ground_for = ' Ground'
            elif brew == 'Drip':
                ground_for = 'Dripper'
            else:
                ground_for = brew
        c.setFont('HookCoffeeClub', 8)
        ground_for_prefix = ELEMENT_POSITION['ground_for'][side]
        c.drawString(ground_for_prefix[0], ground_for_prefix[1], prefix)
        c.setFont('HookCoffeeClub', 16)
        brew_pos = ELEMENT_POSITION['package'][side]
        c.drawString(brew_pos[0], brew_pos[1], ground_for)

    barcode_pos = ELEMENT_POSITION['barcode'][side]
    barcode = _create_qr(order.pk)
    barcode.drawOn(c, *barcode_pos)

    c.showPage()
    c.save()

    page = PdfFileReader(file(template_src, 'rb')).getPage(0)
    overlay = PdfFileReader(StringIO(buffer.getvalue())).getPage(0)
    page.mergePage(overlay)

    return page


def generate_common_product_label(order):
    pdfmetrics.registerFont(AMATIC_BOLD)

    buffer = StringIO()

    width, height = (500, 300)
    c = canvas.Canvas(buffer, pagesize=(width, height))
    c.setLineWidth(.3)
    c.setFont('Amatic-Bold', 36)

    w = width / 2.0

    if isinstance(order, GearOrder):
        recipient = order.shipping_address['recipient_name']
        product_name = order.gear.name
        extra_name = ''
        barcode = _create_qr('G%s' % order.pk)
    elif isinstance(order, RedemItem):
        recipient = order.user.customer.get_full_name()
        product_name = order.item.name
        extra_name = ''
        barcode = _create_qr('R%s' % order.pk)
    else:
        recipient = order.shipping_address['recipient_name']
        product_name = order.coffee.name
        extra_name = 'SHOTPODS' if order.coffee.is_pods else ''
        barcode = _create_qr(order.pk)

    c.drawCentredString(w, 250, recipient)
    c.drawCentredString(w, 160, product_name)
    c.drawCentredString(w, 115, extra_name)
    barcode.drawOn(c, 217, 10)

    c.showPage()
    c.save()

    page = PdfFileReader(StringIO(buffer.getvalue())).getPage(0)
    return page


def print_labels(orders):
    temp = tempfile.TemporaryFile()
    output = PdfFileWriter()
    # try:
    #     allPages = getLabelsQueue()
    #     pageFilesTuples = filter(lambda page: int(page[0][0]) in ids, allPages)
    # except Exception as e:
    #     print 'generated labels directory was not found'
    #     allPages = []
    #     pageFilesTuples = []

    for order_id, order_type in orders:
        if order_type == 'GEAR':
            model = GearOrder
        elif order_type == 'REDEM':
            model = RedemItem
        else:
            model = Order

        order = model.objects.get(id=order_id)
        _add_order_label(order, output)
        # output.addPage(page)
        # try:
        #     # if not precached
        #     if order_id not in [int(pageFileTuple[0][0]) for pageFileTuple in pageFilesTuples]:
        #         output = _get_pdf_output(order)
        #     else:
        #         # check if coffee id has changed
        #         pageTuple = next(pageFileTuple for pageFileTuple in pageFilesTuples if int(pageFileTuple[0][0]) == order_id)
        #         if generate_label_hash(order) != pageTuple[0][1]:
        #             output = _get_pdf_output(order)
        #         else:
        #             # read from the cache if it passes all the failsafes
        #             with file(pageTuple[1], 'rb') as f:
        #                 pageFile = StringIO(f.read())
        #             page = PdfFileReader(pageFile).getPage(0)
        #             output.addPage(page)
        # except:
        #     output = _get_pdf_output(order)


    # print order notes (e.g. Christmas gift note)
    if isinstance(order, GearOrder) and order.details.get('gift_note'):
        page = generate_note(order.details.get('gift_note'))
        output.addPage(page)

    output.write(temp)

    chunk_size = 8192
    wrapper = FileWrapper(temp, chunk_size)

    if len(orders) == 1:
        order_id, _ = orders[0]
        filename = '%s_label.pdf' % order_id
    else:
        filename = 'all_labels.pdf'
    response = StreamingHttpResponse(wrapper, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    response['Content-Length'] = temp.tell()
    temp.seek(0)
    return response


def _add_order_label(order, output):
    if isinstance(order, Order) and order.coffee.is_discovery_pack:
        coffee_ids = order.get_discovery_coffee_ids()
        for coffee_id in coffee_ids:
            page = generate_label(order.id, coffee_id)
            output.addPage(page)
    elif hasOwnLabel(order):
        page = generate_label(order.id)
        output.addPage(page)
    else:
        page = generate_common_product_label(order)
        output.addPage(page)
    return output


def getLabelsQueue():
    # returns a list of tuples (id, file) of all objects on filesystem at STATIC_PATH/labels/<order_id>.pdf
    labels_path = settings.LABELS_PATH
    files_in_dir = os.listdir(labels_path)

    id_and_files = map(lambda file: (getOrderIdAndHashFromFilePath(file), labels_path + file), files_in_dir)
    return id_and_files


def generate_label_hash(order):
    metadata = datetime.strftime(order.coffee.roasted_on, '%d%b%y')
    return hashlib.md5(str(order) + metadata).hexdigest()


def generate_note(text):
    pdfmetrics.registerFont(AMATIC_BOLD)

    buffer = StringIO()

    width, height = (500, 300)
    c = canvas.Canvas(buffer, pagesize=(width, height))
    c.setLineWidth(.3)
    c.setFont('Amatic-Bold', 20) #36

    w = width / 2.0

    vertical_offset = -50
    line_length = 50
    line_height = 30
    text_length = len(text)
    max_lines = height // line_height
    line_count = text_length // line_length + 1
    words = text.split(' ')
    words_per_line = 12

    for j in range(0, line_count):
        c.drawCentredString(
            w,
            vertical_offset + max_lines * line_height - j * line_height,
            " ".join(words[ j * words_per_line : (j+1) * words_per_line ])
            )

    c.showPage()
    c.save()

    page = PdfFileReader(StringIO(buffer.getvalue())).getPage(0)
    return page
