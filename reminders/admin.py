# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.utils import timezone

from .models import Reminder, ReminderSkipDelivery, ReminderSMS

from .admin_helpers import export_csv_ab_reminders, mark_completed


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'email', 'short_order', 'subject', 'template_name',
        'get_created', 'get_resumed', 'get_scheduled', 'completed')
    list_filter = (
        'subject', 'template_name', 'created', 'resumed', 'scheduled',
        'completed')
    search_fields = ('email', 'order__id',)
    raw_id_fields = ('order', )
    actions = [mark_completed]

    def short_order(self, obj):
        order = obj.order
        if order:
            return '%s - %s [%s]' % (
                timezone.localtime(order.date).strftime('%b, %d'),
                timezone.localtime(order.shipping_date).strftime('%b, %d'),
                order.get_status_display(),
            )
        else:
            return None
    short_order.short_description = 'Order'


@admin.register(ReminderSkipDelivery)
class ReminderSkipDeliveryAdmin(admin.ModelAdmin):
    list_display = ('username', 'subject', 'template_name', 'completed',)
    actions = [export_csv_ab_reminders]
    raw_id_fields = ('order', )
    search_fields = ('email',)


@admin.register(ReminderSMS)
class ReminderSMSAdmin(admin.ModelAdmin):
    list_display = ('number', 'scheduled', 'sent',)
    raw_id_fields = ('customer',)
