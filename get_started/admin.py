# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv

from django.contrib import admin
from django.http import HttpResponse
from django.utils.encoding import smart_str

from customers.models import Customer

from .models import *


class MonthListFilter(admin.SimpleListFilter):
    title = 'created in month'
    parameter_name = 'month'

    def lookups(self, request, model_admin):
        return (
            ('jan16', 'January 16'), ('feb16', 'February 16'), ('mar16', 'March 16'),
            ('apr16', 'April 16'), ('may16', 'May 16'), ('jun16', 'June 16'),
            ('jul16', 'July 16'), ('aug16', 'August 16'), ('sep16', 'September 16'),
            ('oct16', 'October 16'), ('nov16', 'November 16'), ('dec16', 'December 16'),
        )

    def queryset(self, request, queryset):
        months = {
            'jan16': (1, 2016), 'feb16': (2, 2016), 'mar16': (3, 2016), 'apr16': (4, 2016),
            'may16': (5, 2016), 'jun16': (6, 2016), 'jul16': (7, 2016), 'aug16': (8, 2016),
            'sep16': (9, 2016), 'oct16': (10, 2016), 'nov16': (11, 2016), 'dec16': (12, 2016)}
        month, year = months.get(self.value(), (0, 0))

        if month and year:
            return queryset.filter(created__month=month, created__year=year)
        else:
            return queryset


def export_csv_response(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=mymodel.csv'

    if not request.user.has_perm('get_started.export_getstartedresponse'):
        return response

    writer = csv.writer(response, csv.excel)
    response.write('\ufeff'.encode('utf8'))

    writer.writerow([
        'id',
        'created',
        'name',
        'email',
        'package',
        'brew_metod',
        'intensity',
        'flavour',
        'ct',
    ])
    for obj in queryset:
        writer.writerow([
            smart_str(obj.id),
            smart_str(obj.created),
            smart_str(obj.name),
            smart_str(obj.email),
            smart_str(obj.form_details.get('default_pack', '')),
            smart_str(obj.form_details.get('brew_title', '')),
            smart_str(obj.form_details.get('intensity', '')),
            smart_str(obj.form_details.get('flavour', '')),
            smart_str(obj.ct),
        ])
    return response
export_csv_response.short_description = 'Export CSV'


def export_csv_not_registered(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=not_registered.csv'

    if not request.user.has_perm('get_started.export_getstartedresponse'):
        return response

    writer = csv.writer(response, csv.excel)
    response.write('\ufeff'.encode('utf8'))

    customer_emails = set(Customer.objects.all().values_list('user__email', flat=True))
    not_registered_responses = queryset.exclude(email__in=customer_emails).order_by('id')
    # not_registered_responses = GetStartedResponse.objects.exclude(email__in=customer_emails).order_by('id')

    writer.writerow([
        'id',
        'created',
        'name',
        'email',
        'form_details',
        'ct',
    ])
    for obj in not_registered_responses:
        writer.writerow([
            smart_str(obj.id),
            smart_str(obj.created),
            smart_str(obj.name),
            smart_str(obj.email),
            smart_str(obj.form_details),
            smart_str(obj.ct),
        ])
    return response
export_csv_not_registered.short_description = "Export user's responses where users have not been registered as customers"


def export_csv_ref_vouchers(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=ref_vouchers.csv'

    if not request.user.has_perm('get_started.export_referralvoucher'):
        return response

    writer = csv.writer(response, csv.excel)
    response.write('\ufeff'.encode('utf8'))

    writer.writerow([
        'sender',
        'used',
        'recipient',
        'discount%',
        'discount$',
        'code',
        'date',
    ])
    for obj in queryset:
        writer.writerow([
            smart_str(obj.sender),
            smart_str(obj.used),
            smart_str(obj.recipient_email),
            smart_str(obj.discount_percent),
            smart_str(obj.discount_sgd),
            smart_str(obj.code),
            smart_str(obj.date),
        ])
    return response


@admin.register(GiftVoucher)
class GiftVoucherAdmin(admin.ModelAdmin):
    readonly_fields = ('created',)


@admin.register(GetStartedResponse)
class GetStartedResponseAdmin(admin.ModelAdmin):
    list_filter = [MonthListFilter, ]
    actions = [export_csv_response, export_csv_not_registered]
    list_display = (
        'name', 'email', 'get_def_pack', 'get_brew', 'get_intensity',
        'get_flavour', 'ct', 'created')
    search_fields = ('name', 'email')

    def get_def_pack(self, obj):
        return obj.form_details.get('default_pack', '')
    get_def_pack.short_description = 'Package'

    def get_brew(self, obj):
        return obj.form_details.get('brew_title', '')
    get_brew.short_description = 'Brew Method'

    def get_intensity(self, obj):
        return obj.form_details.get('intensity', '')
    get_intensity.short_description = 'Intensity'

    def get_flavour(self, obj):
        return obj.form_details.get('flavour', '')
    get_flavour.short_description = 'Flavour'


@admin.register(PodsEarlyBird)
class PodsEarlyBirdAdmin(admin.ModelAdmin):
    readonly_fields = ('date',)


@admin.register(ReferralVoucher)
class ReferralVoucherAdmin(admin.ModelAdmin):
    readonly_fields = ('date',)
    actions = [export_csv_ref_vouchers, ]
    search_fields = ('sender__user__email', 'recipient_email',)
