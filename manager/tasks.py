from __future__ import absolute_import

import os
import os.path
import traceback
from StringIO import StringIO

import hashlib

from PyPDF2 import PdfFileWriter
from celery.schedules import crontab
from celery.task import periodic_task
from django.conf import settings
from django.db.models import Q

from customers.models import Order
from manager import cluster_api
from manager.pdf import addressgenerator, labelgenerator
from manager.utils import deleteExistingOrderLabelPdf, deleteExistingOrderAddressPdf, hasOwnLabel


# @periodic_task(run_every=(crontab(hour="*", minute="*/5", day_of_week="*")))
def generateAddresses():
    try:
        static_path = settings.STATIC_PATH
        template2_src = os.path.join(static_path, 'labels/shipping.pdf')
        template = StringIO(file(template2_src, 'rb').read())

        orders = Order.objects.filter(Q(status='AC') | Q(status='DE') | Q(status='PA'))
        for order in orders:
            try:
                address_path = settings.ADDRESS_PATH
                if not os.path.exists(address_path):
                    os.makedirs(address_path)

                addr_hash = hashlib.md5(order.customer.get_full_address()).hexdigest()
                order_address_file = os.path.join(address_path, '{}.{}.pdf'.format(order.id, addr_hash))

                #if the file does not exist, we generate the file
                if not os.path.exists(order_address_file):
                    #we first delete anything with that id
                    deleteExistingOrderAddressPdf(order.id)

                    #next we create the new pdf
                    page = addressgenerator.generate_address(order)
                    output = PdfFileWriter()
                    output.addPage(page)

                    with open(order_address_file, 'wb') as f:
                        output.write(f)

                else:
                    pass
            except Exception as e:
                print e

    except Exception as e:
        print e



# @periodic_task(run_every=(crontab(hour="*", minute="*/5", day_of_week="*")))
def generateLabels():
    try:
        static_path = settings.STATIC_PATH

        orders = Order.objects.filter(Q(status='AC') | Q(status='DE') | Q(status='PA'))
        for order in orders:
            try:
                labels_path = settings.LABELS_PATH
                if not os.path.exists(labels_path):
                    os.makedirs(labels_path)

                order_hash = labelgenerator.generate_label_hash(order)
                order_label_file = os.path.join(labels_path, '{}.{}.pdf'.format(order.id, order_hash))

                #if the file does not exist, we generate the file
                if not os.path.exists(order_label_file):
                    # we first delete anything with that id
                    deleteExistingOrderAddressPdf(order.id)

                    # next we create the new pdf
                    if hasOwnLabel(order):
                        page = labelgenerator.generate_label(order.id)
                    else:
                        page = labelgenerator.generate_common_product_label(order)
                    output = PdfFileWriter()
                    output.addPage(page)

                    with open(order_label_file, 'wb') as f:
                        output.write(f)

                else:
                    pass
            except Exception as e:
                print e

    except Exception as e:
        print e
        traceback.print_exc()


#cleans up labels which are already shipped
# @periodic_task(run_every=(crontab(hour="0", minute="0", day_of_week="*")))
def cleanUpLabels():
    try:
        order_set = Order.objects.filter(status='SH')

        for order in order_set:
            try:
                deleteExistingOrderLabelPdf(order.id)
            except Exception as e:
                print e
            try:
                deleteExistingOrderAddressPdf(order.id)
            except Exception as e:
                print e

    except Exception as e:
        print e

@periodic_task(run_every=(crontab(hour="0", minute="0", day_of_week="*")))
def doClustering():
    try:
        cluster_api.processExecuteKMeansClusteringForCustomerSegments()

    except Exception as e:
        print e
