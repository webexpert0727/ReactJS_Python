# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.utils import timezone

from registration.models import RegistrationProfile

from admin_helpers import *

from .models import *
from .models.gear_order import GearOrder

from coffees.models import CoffeeType


# Delete selected
# admin.site.disable_action('delete_selected')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    actions = [export_csv_customer, export_csv_customer_intercom, sync_intercom_tags,
        export_subscribers, export_not_ordered, export_unsubscribes, export_reactivation_stages]
    list_display = ('get_email', 'get_full_name', 'get_full_address', 'postcode', 'country',
                    'phone', 'amount', 'get_all_vouchers', 'get_count_orders', 'stripe_id', 'card_details')
    search_fields = ('first_name', 'last_name', 'phone', 'user__email')

    def get_form(self, request, obj=None, **kwargs):
        self.obj = obj
        return super(CustomerAdmin, self).get_form(request, obj, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "vouchers":
            kwargs["queryset"] = Voucher.objects.filter(personal=False).order_by('name')
            if self.obj:
                kwargs["queryset"] |= Voucher.objects.filter(email__iexact=self.obj.user.email)
        return super(CustomerAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    actions = [export_csv_order, ]
    readonly_fields = ('date', )
    # fields = ('customer', 'coffee', 'different', 'shipping_date',\
        # 'amount', 'interval', 'recurrent', 'status', 'brew', 'package',\
        # 'feedback', 'details', 'voucher')
    list_display = ('status', 'get_fmt_creation_date', 'get_fmt_shipping_date',
                    'customer', 'get_customer_country', 'coffee', 'amount', 'brew', 'package',
                    'different', 'recurrent', 'interval', 'voucher', 'feedback')
    list_filter = ('status', 'shipping_date', 'coffee', 'recurrent',)
    search_fields = ('customer__first_name', 'customer__last_name',
                     'customer__phone', 'customer__user__email')
    raw_id_fields = ('customer',)

    class Meta:
        fields = '__all__'

    def get_fmt_creation_date(self, obj):
        return timezone.localtime(obj.date).strftime('%b, %d (%H:%M)')
    get_fmt_creation_date.short_description = 'Creation Date'

    def get_fmt_shipping_date(self, obj):
        return timezone.localtime(obj.shipping_date).strftime('%b, %d (%H:%M)')
    get_fmt_shipping_date.short_description = 'Shipping Date'

    def get_customer_country(self, obj):
        return obj.customer.country
    get_customer_country.short_description = "Country"

    def get_form(self, request, obj=None, **kwargs):
        self.obj = obj
        return super(OrderAdmin, self).get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "coffee":
            kwargs['queryset'] = CoffeeType.objects.active()
            # in case when the coffee is not available anymore
            if self.obj:
                kwargs['queryset'] |= CoffeeType.objects.filter(id=self.obj.coffee.id)
        if db_field.name == "voucher":
            kwargs["queryset"] = Voucher.objects.filter(personal=False).order_by('name')
            if self.obj:
                kwargs["queryset"] |= Voucher.objects.filter(email__iexact=self.obj.customer.user.email)
        return super(OrderAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Preferences)
class PreferencesAdmin(admin.ModelAdmin):
    actions = [export_csv_preferences,]
    list_display = ('customer', 'coffee', 'brew', 'package')
    list_filter = ('customer', 'coffee', 'brew', 'package')

    search_fields = (
        'customer__id',
        'customer__first_name',
        'customer__last_name',
        'customer__phone',
        'customer__user__email',
    )


@admin.register(GearOrder)
class GearOrderAdmin(admin.ModelAdmin):
    actions = (export_csv_gearorders,)
    readonly_fields = ('date',)
    list_display = ('status', 'get_fmt_creation_date', 'get_fmt_shipping_date',
                    'customer', 'gear', 'get_qty', 'price', 'tracking_number', 'is_gift', 'get_address',)
    list_filter = ('status', 'shipping_date', 'gear',)
    search_fields = ('customer__first_name', 'customer__last_name',
                     'customer__phone', 'customer__user__email', 'gear__name', )
    raw_id_fields = ('customer',)

    class Meta:
        fields = '__all__'

    def get_fmt_creation_date(self, obj):
        return timezone.localtime(obj.date).strftime('%b, %d (%H:%M)')
    get_fmt_creation_date.short_description = 'Creation Date'

    def get_fmt_shipping_date(self, obj):
        return timezone.localtime(obj.shipping_date).strftime('%b, %d (%H:%M)')
    get_fmt_shipping_date.short_description = 'Shipping Date'

    def get_qty(self, obj):
        return obj.details.get('Quantity', 1)
    get_qty.short_description = 'Quantity'

    def is_gift(self, obj):
        if obj.address:
            return obj.address.is_gift
        return False

    def get_address(self, obj):
        return obj.address.name if obj.address else 'base'
    get_address.short_description = 'Address'


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'mode', 'personal', )
    list_filter = ('category', 'mode', 'personal',)
    search_fields = ('name', 'email',)
    actions = (personify, unpersonify, )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('customer', 'name', 'recipient_name', 'line1', 'line2',
                    'country', 'postcode', 'is_primary')
    search_fields = ('customer__first_name', 'customer__last_name',
                     'customer__phone', 'customer__user__email')
    raw_id_fields = ('customer',)


@admin.register(CoffeeReview)
class CoffeeReviewAdmin(admin.ModelAdmin):
    actions = (export_csv_coffee_reviews, )
    readonly_fields = ('rating', 'comment', 'coffee', 'order')
    list_display = ('get_short_comment', 'rating', 'coffee', 'order', 'get_fmt_creation_date')
    list_filter = ('rating', 'coffee')
    search_fields = ('order__customer__first_name', 'order__customer__last_name',
                     'order__customer__phone', 'order__customer__user__email',)
    raw_id_fields = ('order',)

    def get_fmt_creation_date(self, obj):
        return timezone.localtime(obj.created_at).strftime('%d/%m/%Y')
    get_fmt_creation_date.short_description = 'Creation Date'

    def get_short_comment(self, obj):
        return (obj.comment[:10] + '...') if obj.comment else '-'
    get_short_comment.short_description = 'Comment'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('customer', 'first_reminder', 'second_reminder', 'last_modified',)


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    search_fields = ('user__email',)


@admin.register(EmailManagement)
class EmailManagementAdmin(admin.ModelAdmin):
    list_display = ('customer', 'order', 'active',)
    raw_id_fields = ('order', 'customer',)
    search_fields = ('customer__user__email',)

@admin.register(Reference)
class ReferenceAdmin(admin.ModelAdmin):
    search_fields = ('referred__email', 'referrer__email',)


admin.site.register(VoucherCategory)
admin.site.register(Postcard)


admin.site.unregister(RegistrationProfile)
