# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import os
from StringIO import StringIO

from PyPDF2 import PdfFileReader, PdfFileWriter

from jsonview.decorators import json_view

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

import stripe

from django.conf import settings
from django.http import HttpResponse

from customers.tasks import send_email_async

from get_started.models import GiftVoucher, ReferralVoucher


stripe.api_key = settings.SECRET_KEY
logger = logging.getLogger('giveback_project.' + __name__)


@json_view
def stripe_send_friend(request):
    context = {
        'success': False,
    }
    token = request.POST['stripeToken']
    recipient = request.POST.get('recipient_name')
    sender_email = request.POST.get('email')
    first_name = request.POST.get('first_name')
    last_name = request.POST.get('last_name')
    credits_amount = request.POST.get('post_credits')
    voucher_code = ReferralVoucher.get_random_code(size=8)

    try:
        charge = stripe.Charge.create(
            amount=int(credits_amount) * 100,
            currency='SGD',
            source=token,
            description='Gift voucher from {} to {}'.format(
                sender_email, recipient)
        )
    except Exception as e:
        raise e
    else:
        GiftVoucher.objects.create(
            sender_email=sender_email,
            sender_fname=first_name,
            sender_lname=last_name,
            recipient=recipient,
            amount=credits_amount,
            code=voucher_code
        )

        # Create a voucher pdf
        static_path = settings.STATIC_PATH
        media_root = settings.MEDIA_ROOT

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=voucher.pdf'

        font_src = os.path.join(static_path, 'fonts/amatic/Amatic-Bold.ttf')
        pdfmetrics.registerFont(TTFont('Amatic-Bold', font_src))

        font_src = os.path.join(static_path, 'fonts/brusher/Brusher-Regular.ttf')
        pdfmetrics.registerFont(TTFont('Brusher-Regular', font_src))

        buffer = StringIO()
        buffer2 = StringIO()

        outfilename = 'voucher_{}.pdf'.format(sender_email)
        outfiledir = os.path.join(media_root, 'gift_vouchers')
        outfilepath = os.path.join(outfiledir, outfilename)

        if not os.path.exists(outfiledir):
            os.makedirs(outfiledir)

        c = canvas.Canvas(buffer)
        c2 = canvas.Canvas(buffer2)

        # c.setLineWidth(.3)
        c.setFont('Amatic-Bold', 60)
        c.drawString(365, 157, '$' + credits_amount)

        c2.setFont('Amatic-Bold', 24)
        c2.drawString(150, 288, voucher_code)

        f_recipient = '{:^12}'.format(recipient)
        if len(recipient) < 9:
            c.setFont('Brusher-Regular', 35)
            c.drawString(75, 250, f_recipient)
        else:
            c.setFont('Brusher-Regular', 28)
            c.drawString(65, 250, f_recipient)

        c.showPage()
        c2.showPage()
        c.save()
        c2.save()

        template_src = os.path.join(static_path, 'vouchers/gift_voucher.pdf')

        page = PdfFileReader(file(template_src, "rb")).getPage(0)
        page2 = PdfFileReader(file(template_src, "rb")).getPage(1)
        overlay = PdfFileReader(StringIO(buffer.getvalue())).getPage(0)
        overlay2 = PdfFileReader(StringIO(buffer2.getvalue())).getPage(0)
        page.mergePage(overlay)
        page2.mergePage(overlay2)

        output = PdfFileWriter()
        output.addPage(page)
        output.addPage(page2)

        output.write(open(outfilepath, 'wb'))

        # Send notification
        send_email_async.delay(
            subject='A Lovely Gift Voucher Within',
            template='Gift Vouchers (done)',
            to_email=sender_email,
            merge_vars={
                'SENDER': first_name,
                'RECEPIENT': recipient,
                'AMOUNT': credits_amount,
                'DOMAIN_NAME': request.META.get('HTTP_HOST'),
            },
            attachments=[(
                outfilename,
                outfilepath,
                'application/pdf'
            )],
        )

        context = {
            'success': True,
        }

    return context
