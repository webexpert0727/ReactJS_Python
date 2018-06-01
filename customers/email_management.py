import logging
import random
import string

from datetime import timedelta

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect

from customers.models import Customer, Order, EmailManagement as EmailManagementObjects
from customers.tasks import add_event
from django.views.generic.edit import FormView
from django.views.generic import UpdateView

from django.utils import timezone

from .forms import SkipDeliveryForm

from manager.utils.order_processing import OrderProcessing

from reminders.models import ReminderSkipDelivery


CTZ = timezone.get_current_timezone()
logger = logging.getLogger('giveback_project.' + __name__)

class EmailManagementView(FormView):

    template_name = 'giveback_project/index.html'
    form_class = None
    success_url = '/accounts/profile/'

    def get(self, request, *args, **kwargs):
        now = CTZ.normalize(timezone.now())
        self.token = self.kwargs.get('token')
        self.object = self.get_object(request)
        if self.object:
            f = self.form_class(request.GET, instance=self.object.order)

            if self.form_valid(f):
                if type(f) == SkipDeliveryForm:
                    f.save()

                    # self.object.order.shipping_date = self.object.order.get_next_shipping_date(
                        # after=self.object.order.shipping_date)
                    # self.object.order.save()

                    if self.object.order.interval >= 7:
                        rsd = ReminderSkipDelivery(
                            username=self.object.order.customer.first_name,
                            order=self.object.order,
                            email=self.object.order.customer.get_email(),
                            from_email='Hook Coffee Roastery <hola@hookcoffee.com.sg>',
                            subject='Your upcoming Hook Coffee Order',
                            template_name=OrderProcessing.EMAIL_REMINDING_TEMPLATE_SKIP_LINK,
                            created=now,
                            # TODO: check scheduled date
                            scheduled=self.object.order.shipping_date - timedelta(days=4),
                        )
                        rsd.save()

                    messages.add_message(request, messages.INFO, "Your subscription shipping date has been changed successfuly", extra_tags="skip")

                    add_event.delay(
                        customer_id=self.object.customer.id,
                        event='skipped',
                        data={
                            'order-id': self.object.order.id,
                            'shipping-date': self.object.order.shipping_date,
                            }
                        )

                    self.object.active = False
                    self.object.save()

        return redirect('profile')


    def get_object(self, request):
        emo = EmailManagementObjects.objects.filter(token=self.token).first()
        if emo and emo.active:
            if emo.action.get('skip'):
                self.form_class = SkipDeliveryForm
            return emo

        else:
            messages.add_message(request, messages.INFO, "Your subscription shipping date was changed earlier", extra_tags="skip")

