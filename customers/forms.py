# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime, timedelta
from itertools import chain

from django_countries.widgets import CountrySelectWidget

import mandrill

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from coffees.models import BrewMethod

from customauth.models import MyUser

from customers.fields import CommaSeparatedEmailField, GoogleContactField
from customers.models import (
    Address, CoffeeReview, Customer, Order,
    Preferences, Referral, Voucher, EmailManagement,
    GearOrder)
from customers.tasks import add_event, send_email_async

from get_started.models import ReferralVoucher

from giveback_project.helpers import get_shipping_date

from loyale.mixin import POINTS_FOR_INVITED_FRIEND, PointMixin
from loyale.models import Item, Point, RedemItem


mandrill_client = mandrill.Mandrill(settings.MANDRILL_API_KEY)
CTZ = timezone.get_current_timezone()
point_mixin = PointMixin()
logger = logging.getLogger('giveback_project.' + __name__)


class CustomerDetailsForm(forms.ModelForm):

    class Meta:
        model = Customer
        fields = ('first_name', 'last_name', 'phone')


class CustomerBaseAddressForm(forms.ModelForm):

    class Meta:
        model = Customer
        fields = ('line1', 'line2', 'postcode')


class AddressForm(forms.ModelForm):

    class Meta:
        model = Address
        # fields = '__all__'
        exclude = ('country', 'customer')


class GiftAddressForm(AddressForm):
    recipient_name = forms.CharField(max_length=128, required=False)
    recipient_first_name = forms.CharField(max_length=128)
    recipient_last_name = forms.CharField(max_length=128)
    unit_number = forms.CharField(max_length=16, required=False)
    note = forms.CharField(
        max_length=600,
        widget=forms.Textarea(
            attrs={'placeholder': _('Leave a message for the recepient'),
                   'class': 'form-control',
                   'rows': '5'}
            ),
        help_text="Write a gift note (600 characters max.)",
        required=False,
        )

    class Meta:
        model = Address
        fields = (
            'recipient_name',
            'recipient_first_name', 'recipient_last_name',
            'line1', 'line2',
            'unit_number', 'postcode',
            )

    def __init__(self, *args, **kwargs):
        if kwargs.get('data'):
            self.order_id = kwargs.get('data').get('order_id', None)
            self.note = kwargs.get('data').get('note', None)

        super(GiftAddressForm, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        cleaned_data = super(GiftAddressForm, self).clean()
        cleaned_data['recipient_name'] = "{} {}".format(
            cleaned_data.get('recipient_first_name'),
            cleaned_data.get('recipient_last_name'))

        self.unit_number = cleaned_data['unit_number']

        return cleaned_data

    def save(self, commit=True):
        instance = super(GiftAddressForm, self).save(commit=False)
        instance.name = "{}'s address".format(instance.recipient_name)
        instance.line2 += " {}".format(self.unit_number)
        if commit:
            instance.save()
            # update order address and details
            try:
                order = GearOrder.objects.get(id=self.order_id)
            except Exception as e:
                logger.error("No gear order ({}) found: {}".format(self.order_id, e))
            else:
                order.address = instance
                order.details['gift_note'] = self.note
                order.save()

        return instance


class ApplyVoucherForm(forms.ModelForm):

    error_messages = {
        'invalid_choice': _('This voucher is not found!'),
        'already_applied': _('For this order a voucher already applied.'),
        'already_used': _('This voucher\'s already used.'),
        'cat_already_used': _('This voucher not applicable for this order.'),
        'special_only': _('Sorry. This voucher code is only applicable for special edition coffee subscriptions'),
        'discovery_only': _('Sorry. This voucher code is only applicable for discovery program subscriptions'),
        'no_bottled': _('Sorry. There are no vouchers applicable for bottled subscriptions at the moment'),
        'introductory_registered': _('Sorry. This is an introductory voucher'),
    }

    voucher = forms.ModelChoiceField(
        queryset=Voucher.objects.select_related('category').filter(mode=True),
        to_field_name='name',
        error_messages=error_messages)

    class Meta:
        model = Order
        fields = ('voucher', )

    def __init__(self, *args, **kwargs):
        self.is_worldwide = kwargs.pop('is_worldwide', None)
        super(ApplyVoucherForm, self).__init__(*args, **kwargs)

    def clean_voucher(self):
        voucher = self.cleaned_data['voucher']
        customer = self.instance.customer
        used_vouchers = (customer.vouchers.select_related('category')
                                          .exclude(category__name='REUSABLE')
                                          .all())
        used_voucher_ct = [v.category.id for v in used_vouchers if v.category]

        # if the customer use `Introductory`, they can't use `Re-engagement`
        # vice versa
        mutually_exclusive = ['Introductory', 'Re-engagement']
        used_mutually_exclusive = (
            used_vouchers
            .filter(category__name__in=mutually_exclusive)
            .exists())

        if self.instance.voucher:
            raise ValidationError(self.error_messages['already_applied'],
                                  code='already_applied')
        elif voucher in used_vouchers:
            raise ValidationError(self.error_messages['already_used'],
                                  code='already_used')
        elif ((voucher.category.id in used_voucher_ct) or
              (voucher.category.name == 'Worldwide' and not self.is_worldwide) or
              (voucher.category.name in mutually_exclusive and used_mutually_exclusive)
              ):
            raise ValidationError(self.error_messages['cat_already_used'],
                                  code='cat_already_used')
        elif voucher.category.name == "special edition coffee" and not self.instance.coffee.special:
            raise ValidationError(self.error_messages["special_only"],
                                  code="special_only")
        elif voucher.category.name == "discover pack" and not self.instance.coffee.is_discovery_pack:
            raise ValidationError(self.error_messages["discovery_only"],
                                  code="discovery_only")
        elif self.instance.coffee.is_bottled():
            raise ValidationError(self.error_messages["no_bottled"],
                                  code="no_bottled")
        elif voucher.category.name == 'Introductory':
            raise ValidationError(self.error_messages["introductory_registered"],
                                  code="introductory_registered")

        three20_voucher_used_times = customer.orders.filter(
            voucher__name='THREE20', status=Order.SHIPPED).count()
        if three20_voucher_used_times > 2:
            raise ValidationError(self.error_messages['already_used'],
                                  code='already_used')

        hook4_voucher_used_times = customer.orders.filter(
            voucher__name='HOOK4', status=Order.SHIPPED).count()
        if hook4_voucher_used_times > 2:
            raise ValidationError(self.error_messages['already_used'],
                                  code='already_used')
        return voucher

    def calculate_new_amount(self):
        voucher = self.cleaned_data['voucher']
        return (self.instance.amount - self.instance.amount *
                voucher.discount / 100 - voucher.discount2)

    def save(self, commit=True):
        if commit:
            voucher = self.cleaned_data['voucher']
            if voucher.name == 'AEROPRESS25':
                self.instance.details[voucher.name] = True
            self.instance.voucher = voucher
            self.instance.amount = self.calculate_new_amount()
            self.instance.save()
            self.instance.customer.vouchers.add(voucher)
            self.instance.customer.save()  # for fire post_save signal
            voucher.count += 1
            voucher.save()
        return self.instance


class CreateOrderForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = ('coffee', 'brew', 'package', 'interval',
                  'different', 'address')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(CreateOrderForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        coffee = self.cleaned_data['coffee']
        self.instance.recurrent = True
        self.instance.amount = coffee.amount
        self.instance.shipping_date = get_shipping_date()
        if self.instance.coffee.is_pods:
            self.request.session['active_tab'] = "active_subscriptions_pods"
        elif self.instance.coffee.is_bottled():
            self.request.session['active_tab'] = "active_subscriptions_bottled"
        else:
            self.request.session['active_tab'] = "active_subscriptions"
        return super(CreateOrderForm, self).save(commit)


class ChangeOrderCoffeeForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = ('coffee',)

    def get_new_amount(self):
        """Recalculate amount for the given order."""
        order = self.instance
        new_coffee = self.cleaned_data['coffee']
        new_amount = (new_coffee.amount if order.recurrent else
                      new_coffee.amount_one_off)
        voucher = order.voucher
        if voucher:
            new_amount = (new_amount - new_amount *
                          voucher.discount / 100 - voucher.discount2)
        return new_amount

    def save(self, commit=True):
        self.instance.amount = self.get_new_amount()
        return super(ChangeOrderCoffeeForm, self).save(commit)


class SkipDeliveryForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = ('shipping_date',)

    def clean_shipping_date(self):
        return self.instance.get_after_next_shipping_date()


class CreateCoffeeReviewForm(forms.ModelForm):

    error_messages = {
        'required': _('Please rate the coffee'),
    }

    rating = forms.IntegerField(
        min_value=1, max_value=5, error_messages=error_messages)

    brew = forms.CharField()

    class Meta:
        model = CoffeeReview
        fields = ('order', 'coffee', 'comment', 'rating', 'brew')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(CreateCoffeeReviewForm, self).__init__(*args, **kwargs)

    def clean_coffee(self):
        order = self.cleaned_data['order']
        if order.coffee.is_discovery_pack:
            return self.cleaned_data['coffee']
        return order.coffee

    def clean_brew(self):
        brew_id = self.cleaned_data['brew']
        try:
            brew = BrewMethod.objects.get(id=brew_id)
        except:
            return
        else:
            return brew

    def clean(self):
        cleaned_data = super(CreateCoffeeReviewForm, self).clean()
        order = self.cleaned_data['order']
        if order.customer_id != self.request.user.customer.id:
            raise ValidationError(
                _("You can't give feedback for someone else's order"))
        return cleaned_data


class OrderPreferencesForm(forms.ModelForm):

    messages = {
        'brew': _('Your order\'s brewing method is changed to <big>%s</big>'),
        'package': _('Your order\'s packaging is changed to <big>%s</big>'),
        'interval': _('You will now receive your coffee every <big>%d</big> days'),
        'different': _('You will now receive <big>%s</big> coffee every time'),
    }

    class Meta:
        model = Order
        fields = ('brew', 'package', 'interval', 'different')
        # widgets = {'brew': forms.HiddenInput()}

    def __init__(self, *args, **kwars):
        super(OrderPreferencesForm, self).__init__(*args, **kwars)
        self.updates = []
        for key in self.fields:
            self.fields[key].required = False

    def clean(self):
        if not self.instance.is_editable:
            raise ValidationError(_(
                'You are unable to change this order as '
                'it is currently being processed.'))
        cleaned_data = super(OrderPreferencesForm, self).clean()

        # FIXME: for pods, field can be empty
        cleaned_data = {k: v for k, v in cleaned_data.items() if v not in ['', None]}
        fields_are_changed = []
        if self.has_changed():
            fields_are_changed = self.changed_data
            # somehow a few fields not really chaned but marked as is
            # so return set with fields are in cleaned_data and changed list
            fields_are_changed = set(cleaned_data) & set(fields_are_changed)

        for field in fields_are_changed:
            if field == 'brew':
                brew = cleaned_data[field].name
                msg = self.messages[field] % brew
            elif field == 'package':
                packages = dict(Preferences.PACKAGE_CHOICES)
                msg = self.messages[field] % packages[cleaned_data[field]]
            elif field == 'interval':
                msg = self.messages[field] % cleaned_data[field]
            elif field == 'different':
                msg = self.messages[field] % (
                    'different' if cleaned_data[field] is True else 'the same')
            self.updates.append(msg)
        return cleaned_data


class CustomerForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=128,
        label=_('First name'),
    )
    last_name = forms.CharField(
        max_length=128,
        label=_('Last name'),
    )

    class Meta:
        model = Customer
        fields = ('first_name', 'last_name', 'country', 'line1', 'line2',
                  'postcode', 'phone',)
        widgets = {
            'country': CountrySelectWidget(
                attrs={'disabled': 'disabled'},
            ),
        }


class GS_CustomerForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=128,
        label=_('First name'),
    )
    last_name = forms.CharField(
        max_length=128,
        label=_('Last name'),
    )

    # FIXME: it's temporary crutches =(
    banned_names = [
        'Zi Ying Choong',
    ]
    banned_addresses = [
        '201, Seragoon Central, #08-12',
        '201, Seragoon Central #08-12',
    ]
    error_messages = {
        'banned': _(
            'Oops, it seems like your account has been compromised. '
            'Please contact us at hola@hookcoffee.com.sg!'),
    }

    class Meta:
        model = Customer
        fields = ('first_name', 'last_name', 'line1', 'line2',
                  'postcode', 'phone',)

        widgets = {'country': CountrySelectWidget()}

    def clean(self):
        cleaned_data = super(GS_CustomerForm, self).clean()
        full_name = ' '.join([
            cleaned_data.get('first_name', '').strip(),
            cleaned_data.get('last_name', '').strip(),
        ])
        full_address = ' '.join([
            cleaned_data.get('line1', '').strip(),
            cleaned_data.get('line2', '').strip(),
        ])

        if ((full_name in self.banned_names) or
            (full_address in self.banned_addresses)):
            raise ValidationError(self.error_messages['banned'], code='banned')
        return cleaned_data


class PreferencesForm(forms.ModelForm):

    customer = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = Preferences
        exclude = ('customer', 'interval', 'cups')

    def __init__(self, no_bottled=False, *args, **kwargs):
        super(PreferencesForm, self).__init__(*args, **kwargs)
        if no_bottled:
            self.fields['package'].choices = Preferences.PACKAGE_CHOICES[:3]

class GS_PreferencesForm(forms.ModelForm):

    customer = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = Preferences
        fields = ('brew', 'package', 'interval', 'different')


class OrderForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = ('brew', 'package',)


class ReferralForm(forms.Form):
    raw_emails = CommaSeparatedEmailField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={'placeholder': _('Enter email, then ‘,’'),
                   'class': 'form-control emails-field js-email-invites-field'}
        )
    )
    google_contacts = GoogleContactField(required=False)

    # reward = Item.objects.get(name='Special surprise for invites')
    spammers = ('yms.tlwf@gmail.com', 'rafaelray.mariano@gmail.com', )

    MAX_INVITES_PER_DAY = 10

    MIN_INVITES_FOR_CHECK_RATE = 10
    MIN_EFFICIENCY_RATE = 10  # in percentages

    EMAIL_SUBJECT = '%s wants to give you $12 towards your first order'
    EMAIL_TEMPLATE = 'REF1'

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.result = {
            'success': False,
            'points_earned': 0,
            'friends_invited': 0,
            'duplicates': 0,
        }
        super(ReferralForm, self).__init__(*args, **kwargs)

    def _remove_duplicates(self, contacts):
        emails = tuple(email for email, name in contacts)
        already_invited = (
            ReferralVoucher.objects.extra(
                where=['lower(recipient_email) IN %s'],
                params=[emails]
            ).values_list('recipient_email', flat=True))
        already_registered = (
            MyUser.objects.extra(
                where=['lower(email) IN %s'],
                params=[emails]
            ).values_list('email', flat=True))
        contacts = [(email, name) for email, name in contacts
                    if email not in chain(already_invited, already_registered)]
        duplicates = len(emails) - len(contacts)
        return contacts, duplicates

    def _get_efficiency_rate(self, total_invited):
        """Return the percent efficiency of invites sent by current customer."""
        total_joined = self.request.user.customer.get_friends_joined()
        return total_joined * 100 / total_invited

    # def _open_rate_is_fine(self):
    #     """FIXME: FOR TESTING PURPOSES ONLY!"""
    #     customer = self.request.user.customer
    #     # check only if the customer send more 20 invites
    #     if customer.get_friends_invited() > 20:
    #         invited_recipients = (
    #             ReferralVoucher.objects.filter(sender=customer)
    #                                    .values_list('recipient_email',
    #                                                 flat=True))
    #         query_string = ''
    #         for email in invited_recipients:
    #             query_string += 'full_email:%s OR ' % email
    #         query_string = query_string.rstrip(' OR ')
    #         # Later will be replaced by searching by metadata field
    #         try:
    #             messages_stats = mandrill_client.messages.search(
    #                 query=query_string, limit=100)
    #         except Exception as e:
    #             logger.error('Mandrill statistics for invites by: %s; %r' % (
    #                          customer, e))
    #         else:
    #             if not messages_stats:
    #                 return True
    #             mes_opened = mes_clicked = 0
    #             for mes in messages_stats:
    #                 mes_opened += 1 if mes.get('opens') else 0
    #                 mes_clicked += 1 if mes.get('clicks') else 0
    #             # if opened less than 40% of the email ivites
    #             # disallow the sending of new invitations
    #             perc_opened = mes_opened * 100 / len(messages_stats)
    #             perc_clicked = mes_clicked * 100 / len(messages_stats)
    #             logger.debug('Stats %s: opened: %s (%s), clicked: %s (%s)' % (
    #                 customer, mes_opened, perc_opened, mes_clicked, perc_clicked))
    #             if perc_opened < 30 or perc_clicked < 10:
    #                 return False
    #     return True

    def _clean_contacts(self, contacts):
        customer = self.request.user.customer
        total_invited = customer.get_friends_invited()
        total_invited_24h = customer.get_friends_invited(
            from_date=datetime.now(tz=CTZ) - timedelta(days=1))

        if not contacts:
            raise ValidationError(
                _('Please select at least one contact.'),
                code='required')
        elif total_invited_24h > self.MAX_INVITES_PER_DAY:
            raise ValidationError(
                _('Sorry! To prevent spam, you can only send out a maximum '
                  'of %(num)d invites each day!'),
                code='limit_exceeded',
                params={'num': self.MAX_INVITES_PER_DAY})
        elif len(contacts) > self.MAX_INVITES_PER_DAY:
            raise ValidationError(
                _('Please select less than %(num)d contacts.'),
                code='limit_exceeded',
                params={'num': self.MAX_INVITES_PER_DAY})
        elif self.request.user.email in self.spammers:
            raise ValidationError(
                _('Sorry! For spam prevention, referrals are currently '
                  'not allowed for your account.'), code='spam')
        elif total_invited > self.MIN_INVITES_FOR_CHECK_RATE:
            rate = self._get_efficiency_rate(total_invited=total_invited)
            if rate < self.MIN_EFFICIENCY_RATE:
                raise ValidationError(
                    _('Error sending invites, please try again later.'),
                    code='low_efficiency')
        # elif not self._open_rate_is_fine():
        #     raise ValidationError(_('Shame on you!'), code='too_much')

        contacts, duplicates = self._remove_duplicates(contacts)

        if not contacts and duplicates == 1:
            raise ValidationError(
                _('Oops! You have invited this friend before!<br/>' +
                  'Spread the love to someone else instead!'),
                code='already_invited')
        elif not contacts and duplicates > 1:
            raise ValidationError(
                _('Oops, all your friends have been invited before.'),
                code='all_invited')
        return contacts, duplicates

    def clean(self):
        cleaned_data = super(ReferralForm, self).clean()
        contacts, duplicates = self._clean_contacts(
            cleaned_data.get('raw_emails') or
            cleaned_data.get('google_contacts'))
        self.cleaned_data['contacts'] = contacts
        self.result['duplicates'] = duplicates
        return self.cleaned_data

    def _send_email(self, customer, recipient_name, recipient_email, ref_link):
        voucher = ReferralVoucher.objects.create(
            sender=customer,
            recipient_email=recipient_email,
            discount_sgd=12,
            code=ReferralVoucher.get_random_code(size=8),
        )
        send_email_async.delay(
            subject=self.EMAIL_SUBJECT % customer.first_name,
            template=self.EMAIL_TEMPLATE,
            to_email=recipient_email,
            from_email='Sam from Hook Coffee <hola@hookcoffee.com.sg>',
            merge_vars={
                'REFNAME': recipient_name or 'there',
                'USERNAME': customer.get_full_name(),
                'LINK': ref_link,
                'VOUCHER': voucher.code,
                'DOMAIN_NAME': self.request.META.get('HTTP_HOST'),
            },
            metadata={
                'by_customer': customer.get_lower_email()
            },
        )

    def send_invites(self):
        user = self.request.user
        customer = user.customer
        contacts = self.cleaned_data.get('contacts', [])

        ref, created = Referral.objects.get_or_create(
            user=user,
            defaults={'code': Referral.get_random_code(customer=customer)}
        )
        ref_link = self.request.build_absolute_uri(ref.get_absolute_url())

        total_invited = customer.get_friends_invited()

        for email, name in contacts:
            try:
                with transaction.atomic():
                    # Send invitation email
                    self._send_email(customer=customer,
                                     recipient_name=name,
                                     recipient_email=email,
                                     ref_link=ref_link)
                    # Grant beanie points for invited friend
                    # ernest asked not to grant points anymore
                    # point_mixin.grant_points(
                    #     user=user, points=POINTS_FOR_INVITED_FRIEND)
                    # Give special surprise for every 20 friends
                    # if (total_invited + 1) % 20 == 0:
                    #     point_mixin.redem_item(user=user, item=self.reward)
            except Exception:
                logger.error('Send ref email. From: %s To: %s',
                             customer, email, exc_info=True)
            else:
                total_invited += 1
                # self.result['points_earned'] += POINTS_FOR_INVITED_FRIEND
                self.result['friends_invited'] += 1

        if self.result['friends_invited']:
            self.result['success'] = True
        add_event.delay(customer_id=customer.id,
                        event='referral-friends',
                        data=self.result)
        return self.result


class RedemForm(PointMixin, forms.ModelForm):

    error_messages = {
        'already': _('Item has already been redeemed'),
        'not_enough': _('Sorry, you have not enough points'),
    }

    class Meta:
        model = RedemItem
        fields = ('item',)

    def __init__(self, *args, **kwargs):
        self.redeemed_item = None
        self.request = kwargs.pop('request')
        super(RedemForm, self).__init__(*args, **kwargs)

    def clean_item(self):
        item = self.cleaned_data['item']
        point = Point.objects.get(user=self.request.user)
        if point.points < item.points:
            raise ValidationError(self.error_messages['not_enough'],
                                  code='not_enough')
        return item

    def save(self, *args, **kwargs):
        item = self.cleaned_data['item']
        if not self.redeemed_item:
            self.redeemed_item = self.redem_item(self.request.user, item)
        return self.redeemed_item
