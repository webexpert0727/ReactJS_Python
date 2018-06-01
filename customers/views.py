# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime, timedelta

from braces.views import (
    JSONResponseMixin, LoginRequiredMixin, SelectRelatedMixin)

from jsonview.decorators import json_view

import stripe

from django import forms
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.messages import get_messages
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.utils import timezone
# from django.utils.dateformat import format as dt_format
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.views.generic import (
    CreateView, DeleteView, FormView, TemplateView, UpdateView, View)

from django.middleware.csrf import get_token

from coffees.models import BrewMethod, CoffeeGear, CoffeeType

from customers.forms import (
    AddressForm, ApplyVoucherForm, ChangeOrderCoffeeForm,
    CreateCoffeeReviewForm,
    CreateOrderForm, CustomerBaseAddressForm,
    CustomerDetailsForm, OrderPreferencesForm,
    PreferencesForm, RedemForm, ReferralForm, GiftAddressForm)
from customers.models import (
    Address, CardFingerprint, CoffeeReview, Customer, GearOrder, Order, Preferences, Referral, WorkShopOrder)
from customers.tasks import (
    add_event, give_points_for_exp_survey, send_email_async,
    sync_cancel_reason)

from giveback_project.helpers import geo_check, get_shipping_date

from loyale.mixin import PointMixin
from loyale.models import Item, Point, RedemItem

from manager.utils import getNextShippingDate
from manager.utils.order_processing import OrderProcessing

from reminders.models import Reminder, ReminderSkipDelivery


CTZ = timezone.get_current_timezone()
stripe.api_key = settings.SECRET_KEY
point_mixin = PointMixin()
logger = logging.getLogger('giveback_project.' + __name__)


class BaseView(LoginRequiredMixin, JSONResponseMixin, FormView):

    http_method_names = ['post']
    success_message = None
    error_message = None

    @method_decorator(geo_check)
    def dispatch(self, request, is_worldwide, *args, **kwargs):
        kwargs.update({'is_worldwide': is_worldwide})
        self.is_worldwide = is_worldwide
        return super(BaseView, self).dispatch(request, *args, **kwargs)

    def get_success_message(self):
        return self.success_message

    def get_error_message(self):
        return self.error_message

    def add_event(self, obj):
        """Fire intercom event"""

    def form_valid(self, form=None, commit=True, **kwargs):
        context = {'success': True, 'message': self.get_success_message()}
        context.update(kwargs)
        obj = None
        if form:
            obj = form.save(commit)
        # FIXME: crutches...
        if (obj or hasattr(self, 'object')):
            self.add_event(obj or self.object)
        return self.render_json_response(context)

    def form_invalid(self, form=None):
        if form:
            errors = form.errors
        else:
            errors = [self.get_error_message()]
        return self.render_json_response({'errors': errors})


class BaseCreateView(BaseView, CreateView):
    pass


class BaseUpdateView(BaseView, UpdateView):

    def get_object_name(self):
        """Return model name in lowercase."""
        return self.model._meta.model_name

    def get_object(self, queryset=None):
        f = forms.IntegerField()
        object_id = f.clean(self.request.POST[self.get_object_name()])
        customer = self.request.user.customer
        return (self.model._default_manager.get(id=object_id,
                                                customer=customer))


class BaseDeleteView(BaseUpdateView, DeleteView):

    def can_delete(self):
        return True

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.can_delete():
            self.object.delete()
            return self.form_valid()
        return self.form_invalid()


class ProfileView(LoginRequiredMixin, TemplateView):
    """Customer's profile."""

    template_name = 'registration/profile.html'

    def _get_addresses_forms(self, customer):
        #
        # temporary crutches to not rewrite all
        # existing code based on one address.
        #
        base_address = {
            'name': 'Base address',
            'recipient_name': customer.get_full_name(),
            'id': -1,
            'is_primary': True,
            'country': customer.country,
            'line1': customer.line1,
            'line2': customer.line2,
            'postcode': customer.postcode,
        }
        additional_addresses = customer.addresses.all()
        if [True for address in additional_addresses if address.is_primary]:
            base_address['is_primary'] = False

        addresses_forms = [AddressForm(initial=base_address)]
        for addr in additional_addresses:
            addresses_forms.append(AddressForm(instance=addr))

        return addresses_forms

    def _get_order_forms(self, customer):
        order_forms = {}
        orders = (
            Order.objects
            .select_related('address', 'brew')
            .filter(customer=customer,
                    recurrent=True,
                    status__in=[Order.ACTIVE, Order.PAUSED, Order.DECLINED]))
        for order in orders:
            order_forms[order.id] = OrderPreferencesForm(instance=order)
        return order_forms

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        now = CTZ.normalize(timezone.now())
        day = now.isoweekday()

        user = self.request.user
        customer, _ = Customer.objects.get_or_create(
            user=user,
            defaults={},
        )
        preferences, _ = Preferences.objects.get_or_create(
            customer=customer,
            defaults={},
        )

        if day in [1, 2, 3, 4, 7]:  # isoweekdays
            context['shipping_tmr'] = timezone.now() + timedelta(days=1)
        else:
            context['shipping_tmr'] = False

        context['customer_details_form'] = CustomerDetailsForm(
            instance=customer, label_suffix='')
        context['referral_form'] = ReferralForm()
        context['addresses_forms'] = self._get_addresses_forms(customer)
        context['order_forms'] = self._get_order_forms(customer)
        context['new_address_form'] = AddressForm(initial={
            'recipient_name': customer.get_full_name()})
        context['preferences_form'] = PreferencesForm(no_bottled=True)

        # brew_methods = BrewMethod.objects.sorted()
        brew_methods = BrewMethod.objects.all().order_by('id')
        brew_none = [brew for brew in brew_methods
                     if brew.name_en == 'None'][0]
        brew_nespresso = [brew for brew in brew_methods
                          if brew.name_en == 'Nespresso'][0]
        brew_non_nespresso = [brew for brew in brew_methods
                              if brew.name_en != 'Nespresso']
        brew_bottled = [brew for brew in brew_methods
                            if brew.name_en == 'Cold Brew'][0]

        context['brew_methods'] = brew_non_nespresso
        context['free'] = preferences.present_next
        context['coffees'] = [x for x in CoffeeType.objects.bags() if not x.is_bottled()]
        context['coffees_pods'] = CoffeeType.objects.nespresso()
        context['coffees_bottled'] = CoffeeType.objects.bottled()
        context['coffee_rating'] = CoffeeType.objects.avg_rating()
        context['new_order_form_bags'] = CreateOrderForm(initial={
            'coffee': context['coffees'][0],
            'brew': brew_none,
            'different': False,
        })
        context['new_order_form_pods'] = CreateOrderForm(initial={
            'coffee': context['coffees_pods'][0],
            'brew': brew_nespresso,
            'package': Preferences.DRIP_BAGS,
            'different': False,
        })
        context['new_order_form_bottled'] = CreateOrderForm(initial={
            'coffee': context['coffees_bottled'][0],
            'brew': brew_bottled,
            'package': Preferences.BOTTLED,
            'different': False,
        })
        context['orders'] = (
            Order.objects
            .select_related('address', 'brew')
            .filter(customer=customer,
                    recurrent=True,
                    status__in=[Order.ACTIVE, Order.PAUSED, Order.DECLINED])
            .exclude(brew=brew_nespresso)
            .exclude(package=Preferences.BOTTLED)
            )
        context['orders_pods'] = (
            Order.objects
            .select_related('address', 'brew')
            .filter(customer=customer,
                    recurrent=True,
                    status__in=[Order.ACTIVE, Order.PAUSED, Order.DECLINED],
                    brew=brew_nespresso))
        context['orders_bottled'] = (
            Order.objects
            .select_related('address', 'brew')
            .filter(customer=customer,
                    recurrent=True,
                    status__in=[Order.ACTIVE, Order.PAUSED, Order.DECLINED],
                    brew=brew_bottled,
                    package=Preferences.BOTTLED))
        context['gear_orders'] = (
            GearOrder.objects
            .select_related('gear')
            .filter(customer=customer,
                    status__in=[Order.ACTIVE, Order.DECLINED, Order.ERROR]))
        context['workshop_orders'] = (
            WorkShopOrder.objects
            .select_related('workshop')
            .filter(customer=customer,
                    status__in=[Order.ACTIVE, Order.DECLINED, Order.ERROR]))
        context['history'] = (
            Order.objects
            .select_related('coffee', 'brew')
            .prefetch_related('reviews')
            .filter(customer=customer, status=Order.SHIPPED))
        # previous_month = now.replace(day=1) - timedelta(days=1)
        # context['best_sellers'] = {
        #     'month': dt_format(previous_month, 'M'),
        #     'coffee': (
        #         CoffeeType.objects
        #         .bags()
        #         .best_seller(order__date__month=previous_month.month)),
        #     'coffee_pods': (
        #         CoffeeType.objects
        #         .nespresso()
        #         .best_seller(order__date__month=previous_month.month)),
        # }
        context['gears_recommend'] = (
            CoffeeGear.objects
            .prefetch_related('images')
            .filter(recommend=True))
        context['redemption_history'] = (
            RedemItem.objects.filter(user=user))
        context['gear_history'] = (
            GearOrder.objects
            .select_related('gear')
            .filter(customer=customer,
                    status=GearOrder.SHIPPED)
            .prefetch_related('gear__images'))
        context['alacartes'] = (
            Order.objects
            .filter(customer=customer,
                    recurrent=False,
                    status__in=[Order.ACTIVE, Order.DECLINED, Order.ERROR]))
        context['redeem_items'] = (
            Item.objects.filter(in_stock=True)
                        .exclude(name='Free bag of coffee')
                        .exclude(name='Special surprise for invites')
        )
        point, _ = Point.objects.get_or_create(
            user=user,
            defaults={'points': 0},
        )
        context['points'] = point.points

        free_bag_item = Item.objects.filter(name='Free bag of coffee')
        if free_bag_item.exists():
            context['free_bag_item'] = free_bag_item[0]
        context['redemed_points'] = point_mixin.redemed_points(user=user)
        context['accumulated_points'] = point_mixin.accumulated_points(user=user)

        context['customer'] = customer
        context['last4'] = customer.card_details[:4]
        if len(customer.card_details) > 9:
            context['exp_month'] = customer.card_details[4:6]
            context['exp_year'] = customer.card_details[6:]
        else:
            context['exp_month'] = '{:0>2}'.format(customer.card_details[4:5])
            context['exp_year'] = customer.card_details[5:]

        ref, _ = Referral.objects.get_or_create(
            user=user,
            defaults={'code': Referral.get_random_code(customer=customer)}
        )
        context['ref_link'] = self.request.build_absolute_uri(ref.get_absolute_url())
        context['stripe_key'] = settings.PUBLISHABLE_KEY
        context['the_code'] = ref.code

        context['active_tab'] = self.request.session.get('active_tab', 'active_subscriptions')

        new_purchase_amount = self.request.session.pop('new_purchase_amount', None)
        context['new_purchase_amount'] = new_purchase_amount

        context['stripe_notification'] = self.request.session.pop('stripe-notification', None)
        # show the customer survey only after 14 days after
        # the customer made the first order
        now = CTZ.normalize(timezone.now())
        gte_14_days_after_reg = now > (customer.user.created_at + timedelta(days=14))
        already_answered_exp_survey = customer.extra.get('answered_exp_survey', False)
        context['show_customer_survey'] = bool(
            not already_answered_exp_survey and gte_14_days_after_reg)
        context['pagename'] = 'profile'

        for message in get_messages(self.request):
            if message.extra_tags == 'skip':
                context['skip'] = message

        return context

    @method_decorator(geo_check)
    def dispatch(self, request, is_worldwide, *args, **kwargs):
        kwargs.update({'is_worldwide': is_worldwide})
        return super(ProfileView, self).dispatch(request, *args, **kwargs)


class UpdateCustomerDetails(BaseUpdateView):
    """Update customer's account details."""

    model = Customer
    form_class = CustomerDetailsForm
    success_message = _('Profile successfully updated')

    def get_object(self, queryset=None):
        return self.request.user.customer


class ChangeCustomerPassword(BaseUpdateView):
    """Change customer's password."""

    model = Customer
    form_class = PasswordChangeForm
    success_message = _('Password successfully updated')

    def get_object(self, queryset=None):
        return self.request.user

    def get_form_kwargs(self):
        return {'user': self.get_object(),
                'data': self.request.POST}


class CreateAddress(BaseCreateView):
    """Create new customer's address."""

    model = Address
    fields = ['recipient_name', 'name', 'line1', 'line2', 'postcode']
    success_message = _('Address created successfully!')

    def add_event(self, obj):
        add_event.delay(
            customer_id=obj.customer_id,
            event='created_address',
            data={'address': {
                'value': str(obj),
                'url': ('https://hookcoffee.com.sg/admin/customers/address'
                        '/%d/' % obj.id)}})

    def form_valid(self, form):
        form.instance.customer = self.request.user.customer
        address = model_to_dict(form.save(), exclude=['country'])
        return super(CreateAddress, self).form_valid(
            form, commit=False, address=address)


class CreateGiftAddress(BaseCreateView):
    """Create address for a gift."""

    model = Address
    form_class = GiftAddressForm
    success_message = _('Address created successfully!')

    def add_event(self, obj):
        add_event.delay(
            customer_id=obj.customer_id,
            event='created_address',
            data={'address': {
                'value': str(obj),
                'url': ('https://hookcoffee.com.sg/admin/customers/address'
                        '/%d/' % obj.id)}})

    def form_valid(self, form):
        form.instance.customer = self.request.user.customer
        form.instance.is_gift = True
        address = model_to_dict(form.save(), exclude=['country'])
        return super(CreateGiftAddress, self).form_valid(
            form,
            commit=False,
            address=address,
            note=form.data.get('note'),
            token=get_token(self.request))


class UpdateAddress(BaseUpdateView):
    """Update customer's address."""

    model = Address
    fields = ['recipient_name', 'name', 'line1', 'line2', 'postcode']
    success_message = _('Address updated successfully!')

    def get_object(self, queryset=None):
        f = forms.IntegerField()
        address_id = f.clean(self.request.POST['address'])
        if address_id == -1:
            return None
        return (self.model._default_manager
                          .get(id=address_id,
                               customer=self.request.user.customer))

    def get_form(self, form_class=None):
        f = forms.IntegerField()
        address_id = f.clean(self.request.POST['address'])
        if address_id == -1:
            # base address; use customer form/model for update
            return CustomerBaseAddressForm(
                self.request.POST, instance=self.request.user.customer)
        else:
            # additional address
            return super(UpdateAddress, self).get_form()


class DeleteAddress(BaseDeleteView):
    """Delete customer's address."""

    model = Address
    success_message = _('Address deleted successfully!')
    error_message = _('Oops! You have an active subscription to this address!')

    def add_event(self, obj):
        add_event.delay(
            customer_id=obj.customer_id,
            event='deleted_address',
            data={'address': str(obj)})

    def can_delete(self):
        if self.object.orders.count() > 0:
            return False
        return True


class ChangePrimaryAddress(BaseUpdateView):
    """Change customer's primary address."""

    model = Address
    fields = ['is_primary']
    success_message = _('Primary address changed successfully!')

    def get_form_kwargs(self):
        kwargs = super(ChangePrimaryAddress, self).get_form_kwargs()
        kwargs.update({'data': {'is_primary': True}})
        return kwargs

    def post(self, request, *args, **kwargs):
        f = forms.IntegerField()
        address_id = f.clean(self.request.POST['address'])
        if address_id == -1:
            return self.form_valid(None)
        return super(ChangePrimaryAddress, self).post(request, *args, **kwargs)

    def add_event(self, obj):
        # will not be called if it's base address (address_id == -1)
        add_event.delay(
            customer_id=obj.customer_id,
            event='changed_primary_address',
            data={'primary_address': {
                'value': str(obj),
                'url': ('https://hookcoffee.com.sg/admin/customers/address'
                        '/%d/' % obj.id)}})

    def form_valid(self, form):
        # before we save new primary address, mark all existing as not primary
        (self.model._default_manager
                   .filter(customer=self.request.user.customer)
                   .update(is_primary=False))
        return super(ChangePrimaryAddress, self).form_valid(form)


class CreateOrder(BaseCreateView):
    """Create new customer's order."""

    model = Order
    form_class = CreateOrderForm

    def get_form_kwargs(self):
        kwargs = super(CreateOrder, self).get_form_kwargs()
        f = forms.IntegerField()
        address_id = f.clean(self.request.POST['address'])

        if address_id == -1:
            data = self.request.POST.copy()
            data['address'] = None
            kwargs.update({'data': data})

        kwargs.update({'request': self.request})
        return kwargs

    def add_event(self, obj):
        add_event.delay(
            customer_id=obj.customer_id,
            event=('created-subscription' if obj.recurrent else
                   'created-one-off'),
            order_id=obj.id)

    def form_valid(self, form):
        form.instance.customer = self.request.user.customer
        return super(CreateOrder, self).form_valid(form)


class UpdateOrderPreferences(BaseUpdateView):
    """Update customer's order preferences."""

    model = Order
    form_class = OrderPreferencesForm

    def add_event(self, obj):
        updates = dict([('Msg %d' % i, msg)
                        for i, msg in enumerate(self.updates)])
        add_event.delay(
            customer_id=obj.customer_id,
            event='changed-order-preferences',
            data=updates,
            order_id=obj.id)

    def form_valid(self, form):
        self.updates = form.updates
        return (super(UpdateOrderPreferences, self)
                .form_valid(form, message=form.updates))


class CreateOrderCoffeeReview(BaseCreateView):
    """Leave a review and rate for order coffee."""

    model = CoffeeReview
    form_class = CreateCoffeeReviewForm
    success_message = _('Thank you for feedback!')

    def get_form_kwargs(self):
        kwargs = super(CreateOrderCoffeeReview, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

    def add_event(self, obj):
        add_event.delay(
            customer_id=obj.order.customer_id,
            event='leave_coffee_review',
            data={'rating': obj.rating, 'comment': obj.comment, 'used brew': obj.brew.name},
            order_id=obj.order_id)


class ChangeOrderCoffee(BaseUpdateView):
    """Change order coffee."""

    model = Order
    form_class = ChangeOrderCoffeeForm
    success_message = _('Coffee successfully changed!')

    def add_event(self, obj):
        add_event.delay(
            customer_id=obj.customer_id,
            event='update-subscription',
            order_id=obj.id)

    def form_valid(self, form):
        amount = form.get_new_amount()
        return super(ChangeOrderCoffee, self).form_valid(form, price=amount)


class ChangeOrderShippingDate(BaseUpdateView):
    """Change order shipping date."""

    model = Order
    fields = ['shipping_date']
    success_message = _('Shipping date successfully changed!')

    def get_form_kwargs(self):
        kwargs = super(ChangeOrderShippingDate, self).get_form_kwargs()
        f = forms.CharField()
        new_date = (
            datetime
            .strptime(f.clean(self.request.POST['newDate']), '%d/%m/%Y')
            .replace(hour=12, minute=0, second=0, microsecond=0))
        kwargs.update({'data': {'shipping_date': new_date}})
        return kwargs

    def form_valid(self, form):
        now = CTZ.normalize(timezone.now())

        ReminderSkipDelivery.objects.filter(order=self.object).update(completed=True)

        if (self.object.shipping_date - now).days >= 7:
            rsd = ReminderSkipDelivery(
                username=self.object.customer.first_name,
                order=self.object,
                email=self.object.customer.get_email(),
                from_email='Hook Coffee Roastery <hola@hookcoffee.com.sg>',
                subject='Your upcoming Hook Coffee Order',
                template_name=OrderProcessing.EMAIL_REMINDING_TEMPLATE_SKIP_LINK,
                created=now,
                scheduled=self.object.shipping_date - timedelta(days=4),
            )
            rsd.save()

        return super(ChangeOrderShippingDate, self).form_valid(form)

    # TODO: move code from front-end
    # def add_event(self, obj):


class PauseOrResumeOrder(BaseUpdateView):
    """Pause or resume a customer's order."""

    model = Order
    fields = ['status', 'shipping_date']

    def get_form_kwargs(self):
        kwargs = super(PauseOrResumeOrder, self).get_form_kwargs()
        if self.object.is_paused:
            new_status = self.model.ACTIVE
            shipping_date = get_shipping_date()
        else:
            new_status = self.model.PAUSED
            shipping_date = self.object.shipping_date + timedelta(days=28)
        kwargs.update({'data': {
            'status': new_status,
            'shipping_date': shipping_date,
        }})
        return kwargs

    # TODO: move code from front-end
    # def add_event(self, obj):

    def form_valid(self, form):
        new_date = datetime.strftime(self.object.shipping_date, '%d of %B, %Y')
        if self.object.is_paused:  # status already updated
            reminder, _ = Reminder.objects.update_or_create(
                order=self.object,
                defaults={
                    'username': self.object.customer.first_name,
                    'email': self.object.customer.user.email,
                    'order': self.object,
                    'from_email': 'Hook Coffee <hola@hookcoffee.com.sg>',
                    'subject': ('Welcome back! Your paused subscription '
                                'is to be resumed.'),
                    'template_name': 'Paused subscription to be resumed',
                    'resumed': self.object.shipping_date,
                    'scheduled': self.object.shipping_date - timedelta(days=3),
                    'completed': False,
                }
            )
            send_email_async.delay(
                subject='Your subscription has been paused',
                template='Paused Subscription (done)',
                to_email=self.object.customer.get_email(),
                merge_vars={
                    'USERNAME': self.object.customer.first_name,
                    'SHIPPING_DATE': new_date,
                    'DOMAIN_NAME': self.request.META.get('HTTP_HOST'),
                })
        else:
            (Reminder.objects.filter(email=self.object.customer.get_email(),
                                     order=self.object)
                             .update(completed=True))
        return super(PauseOrResumeOrder, self).form_valid(form, new_date=new_date)


class CancelOrder(SelectRelatedMixin, BaseUpdateView):
    """Cancel a customer's order.

    - Recurrent orders (subscription)
    - One-off orders
    - Gear orders
    """

    fields = ['status']
    select_related = ['customer', 'customer__user']

    @cached_property
    def model(self):
        is_gear_order = self.request.POST.get('isGear') == 'true'
        return GearOrder if is_gear_order else Order

    def get_form_kwargs(self):
        kwargs = super(CancelOrder, self).get_form_kwargs()
        kwargs.update({'data': {'status': self.model.CANCELED}})
        return kwargs

    def add_event(self, obj):
        if isinstance(obj, Order):
            event = ('canceled-subscription' if obj.recurrent else
                     'cancel-one-off')
            add_event.delay(
                customer_id=obj.customer.id,
                event=event, order_id=obj.id)
        else:
            event = 'cancel-gear-order'
            add_event.delay(
                customer_id=obj.customer.id,
                event=event,
                data={'gear': {
                    'value': obj.gear.name,
                    'url': ('https://hookcoffee.com.sg/admin/customers/gearorder'
                            '/%d/' % obj.id)}}
            )

    def form_valid(self, form):
        if isinstance(self.object, Order) and self.object.recurrent:
            # Mark related to the order reminders as completed
            Reminder.objects.filter(order=self.object).update(completed=True)
            ReminderSkipDelivery.objects.filter(order=self.object).update(completed=True)

            sync_cancel_reason.apply_async(
                (self.object.customer.id, self.object.id, ), countdown=180)  # run in 3 minutes

            send_email_async.delay(
                subject='We are sorry to see you leave',
                template='Cancelled Subscription (done)',
                to_email=self.object.customer.get_email(),
                merge_vars={
                    'USERNAME': self.object.customer.first_name,
                    'DOMAIN_NAME': self.request.META.get('HTTP_HOST'),
                })
        return super(CancelOrder, self).form_valid(form)


class ChangeOrderAddress(BaseUpdateView):
    """Change order address."""

    model = Order
    fields = ['address']
    success_message = _('Address changed successfully!')

    def post(self, request, *args, **kwargs):
        f = forms.IntegerField()
        self.address_id = f.clean(self.request.POST['address'])
        if self.address_id == -1:
            self.object = self.get_object()
            return self.form_valid(None)
        else:
            return super(ChangeOrderAddress, self).post(request, *args, **kwargs)

    def add_event(self, obj):
        add_event.delay(
            customer_id=obj.customer_id,
            event='changed_order_shipping_address',
            order_id=obj.id)

    def form_valid(self, form):
        if form:
            if 'force_base_address' in self.object.details:
                del self.object.details['force_base_address']
        else:
            # the customer trying to change address to `base address`
            # which can differ from primary address
            self.object.details['force_base_address'] = True
            self.object.address = None
            self.object.save()
            # FIXME after that save again?
        return super(ChangeOrderAddress, self).form_valid(form)


class AnsweredExpSurvey(LoginRequiredMixin, View):
    """Mark a customer as answered on the exp survey."""

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        customer = request.user.customer
        already_answered = customer.extra.get('answered_exp_survey', False)
        if already_answered:
            logger.info(
                'User %s trying to submit the exp survey more than once.' %
                customer)
            return HttpResponse(status=200)

        customer.extra['answered_exp_survey'] = True
        customer.save()

        # Give beanie points in 24h, when the system get his answers
        give_points_for_exp_survey.apply_async(
            (customer.id, ), countdown=180)  # run in 2 minutes

        # Fire intercom event
        add_event.delay(
            customer_id=customer.id,
            event='answered-the-exp-survey')
        return HttpResponse(status=200)


class ApplyVoucher(BaseUpdateView):
    """Apply voucher to order."""

    model = Order
    form_class = ApplyVoucherForm
    success_message = _('Voucher applied successfully!')

    def get_form_kwargs(self):
        kwargs = super(ApplyVoucher, self).get_form_kwargs()
        data = self.request.POST.copy()
        data['voucher'] = data.get('voucher', '').strip().upper()
        kwargs.update({
            'is_worldwide': self.is_worldwide,
            'data': data,
        })
        return kwargs

    def form_valid(self, form):
        amount = form.calculate_new_amount()
        return super(ApplyVoucher, self).form_valid(form, price=amount)


class ReferralFriends(LoginRequiredMixin,
                      JSONResponseMixin,
                      FormView):
    """Send invites to customer's friends."""

    http_method_names = ['post']
    form_class = ReferralForm

    def get_form_kwargs(self):
        kwargs = super(ReferralFriends, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

    def form_valid(self, form):
        return self.render_json_response(form.send_invites())

    def form_invalid(self, form):
        return self.render_json_response({'errors': form.errors})


class CreateRedem(BaseView):
    """Create a new redem for customer."""

    form_class = RedemForm
    success_message = _('Your redemption is currently being processed!')

    def get_form_kwargs(self):
        kwargs = super(CreateRedem, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

    def add_event(self, obj):
        add_event.delay(
            customer_id=obj.user.customer.id,
            event='redeemed-reward',
            data={'redem': {
                'value': obj.item.name,
                'url': ('https://hookcoffee.com.sg/admin/loyale/redemitem'
                        '/%d/' % obj.id)}}
        )

    def form_valid(self, form):
        redeemed_item = form.save(commit=False)
        if redeemed_item.item.name == 'Free bag of coffee':
            prefs = self.request.user.customer.preferences
            prefs.present_next = True
            prefs.save()
            redeemed_item.status = 'done'
            redeemed_item.save(update_fields=['status'])
        return super(CreateRedem, self).form_valid(
            form, commit=False, points_spent=redeemed_item.points)


@json_view
def change_stripe(request):
    customer = request.user.customer
    token = request.POST.get('stripeToken')

    logger.debug("Customer \"{}\" tries to edit credit card details, token \"{}\"".format(customer, token))

    if token:
        # revoke email from Stripe
        try:
            stripe_user = stripe.Customer.retrieve(customer.stripe_id)
            stripe_user.metadata['previous email'] = customer.user.email
            stripe_user.email = None
            stripe_user.save()
        except Exception as e:
            logger.error("Failed to retrieve Stripe user\n{}".format(e))

        # create new Stripe user with the same email
        try:
            stripe_customer = stripe.Customer.create(
                source=token,
                email=customer.user.email,
                description='{} {}'.format(
                    customer.first_name,
                    customer.last_name
                    ),
                )
            customer.stripe_id = stripe_customer.id

            stripe_data = stripe_customer.to_dict()
            last4 = stripe_data['sources']['data'][0]['last4']

            customer.card_details = '{}{}{}'.format(
                last4,
                '{:0>2}'.format(
                    stripe_data['sources']['data'][0]['exp_month']),
                stripe_data['sources']['data'][0]['exp_year']
                )
            customer.save()

            card = stripe_data['sources']['data'][0]
            fingerprint = card['fingerprint']
            CardFingerprint.objects.create(
                customer=customer,
                fingerprint=fingerprint,
            )

            # retrieve customer's latest order. If order has status 'DE', create new order for customer
            try:
                order = Order.objects.filter(customer=customer).latest('shipping_date')
            except Order.DoesNotExist as e:
                order = None
            else:
                if order.status == 'DE':
                    try:
                        Order.objects.create(
                            customer=customer,
                            coffee=order.coffee,
                            date=datetime.now(),
                            shipping_date=getNextShippingDate(order.shipping_date, None), # shipping date to be tomorrow's date
                            amount=order.amount,
                            interval=order.interval,
                            recurrent=order.recurrent,
                            status=Order.ACTIVE,
                            brew=order.brew,
                            package=order.package,
                            different=order.different,
                            voucher=order.voucher
                        )
                    except Exception as e:
                        logger.error("Failed to create new order for {}\n{}".format(customer, e))

            logger.debug("Successfully updated credit card details for customer \"{}\" - **** **** **** {}".format(customer, last4))

            return {
                'success': True,
            }
        except stripe.error.StripeError as e:
            body = e.json_body
            err  = body['error']
            logger.error("Failed to update credit card details for customer \"{}\"\n{}{}{}".format(
                customer, err.get('code'), err.get('decline_code'), err.get('message')))

            return {
                'success': False,
                'message': err.get('message'),
            }
        except Exception as e:
            logger.error("Failed to update credit card details for customer \"{}\"\n{}".format(customer, e))
            return {
                'success': False,
                'message': "Failed to update credit card details",
            }

    return {
                'success': False,
            }
