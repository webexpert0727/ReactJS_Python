# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import tempfile
from StringIO import StringIO
from wsgiref.util import FileWrapper

from PyPDF2 import PdfFileWriter, PdfFileReader

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from django.conf import settings
from django.http import StreamingHttpResponse

from customers.models import Postcard


HOOKCOFFEE_CLUB = TTFont(
    'HookCoffeeClub', os.path.join(settings.STATIC_PATH,
                                   'fonts/HookCoffee Club.ttf'))


def generate_postcard(customer):
    pdfmetrics.registerFont(HOOKCOFFEE_CLUB)

    greeting = 'HOLA %s !' % customer.first_name
    greeting_position = (475, 1300)
    postcard = Postcard.objects.latest('id').customer_postcard
    template_src = os.path.join(settings.MEDIA_ROOT, str(postcard))

    buffer = StringIO()

    c = canvas.Canvas(buffer)
    c.setLineWidth(.3)

    c.setFont('HookCoffeeClub', 96)
    x, y = greeting_position
    c.drawCentredString(x, y, greeting)

    c.showPage()
    c.save()

    page = PdfFileReader(file(template_src, 'rb')).getPage(0)
    overlay = PdfFileReader(StringIO(buffer.getvalue())).getPage(0)
    page.mergePage(overlay)

    return page


def print_postcards(customers):
    temp = tempfile.TemporaryFile()
    output = PdfFileWriter()

    for customer in customers:
        page = generate_postcard(customer)
        output.addPage(page)
    output.write(temp)

    chunk_size = 8192
    wrapper = FileWrapper(temp, chunk_size)

    if len(customers) == 1:
        customers_id = customers[0].id
        filename = 'cus_%s_postcard.pdf' % customers_id
    else:
        filename = 'all_postcards.pdf'
    response = StreamingHttpResponse(wrapper, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    response['Content-Length'] = temp.tell()
    temp.seek(0)
    return response
