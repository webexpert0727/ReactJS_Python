# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from adminsortable.admin import SortableAdmin

from modeltranslation.admin import TabbedDjangoJqueryTranslationAdmin

from django import forms
from django.contrib import admin

from coffees.models import *


@admin.register(CoffeeType)
class CoffeeTypeAdmin(TabbedDjangoJqueryTranslationAdmin, SortableAdmin):
    list_filter = ('mode',)
    list_display = ('name', 'region', 'country', 'amount', 'amount_one_off', 'mode', 'special', 'discovery', 'decaf')
    fieldsets = (
        (None, {
            'fields': ('name', 'mode', 'unavailable', 'special', 'discovery', 'decaf', 'blend', 'amount', 'amount_one_off', 'weight')
        }),
        ('Production', {
            'fields': ('maker', ('country', 'region'), ('altitude', 'varietal', 'process')),
        }),
        ('Taste', {
            'fields': ('recommended_brew', 'taste', 'more_taste', 'body', 'intensity', 'acidity', 'profile'),
        }),
        ('Details', {
            'fields': ('brew_method', 'description', 'roasted_on', 'shipping_till')
        }),
        ('Files', {
            'fields': ('img', 'img_moreinfo', 'label', 'label_drip', 'label_position', )
        }),
    )

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name.startswith('description_'):
            kwargs['widget'] = forms.Textarea()
        return super(CoffeeTypeAdmin, self).formfield_for_dbfield(db_field, **kwargs)


class CoffeeGearForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = CoffeeGear
        fields = '__all__'


class CoffeeGearImageInline(admin.TabularInline):
    model = CoffeeGearImage
    extra = 1


@admin.register(CoffeeGear)
class CoffeeGearAdmin(TabbedDjangoJqueryTranslationAdmin, SortableAdmin):
    list_display = ('name', 'model', 'price', 'essentials',
                    'in_stock', 'available', 'recommend')
    inlines = (CoffeeGearImageInline, )

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name.startswith('description_'):
            kwargs['widget'] = forms.Textarea()
        return super(CoffeeGearAdmin, self).formfield_for_dbfield(db_field, **kwargs)


@admin.register(BrewMethod)
class BrewMethodAdmin(TabbedDjangoJqueryTranslationAdmin):
    pass


admin.site.register(Flavor)
admin.site.register(CoffeeSticker)
admin.site.register(SharedCoffeeSticker)
admin.site.register(CoffeeGearColor)
admin.site.register(FarmPhotos)
admin.site.register(WorkShopDates)
admin.site.register(WorkShops)
admin.site.register(CourseCategory)
