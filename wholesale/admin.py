from adminsortable.admin import SortableAdmin

from django.contrib import admin

from modeltranslation.admin import TabbedDjangoJqueryTranslationAdmin

from .models import *


@admin.register(Plan)
class PlanAdmin(TabbedDjangoJqueryTranslationAdmin, SortableAdmin):
    list_display = ('name', 'office_type',)
