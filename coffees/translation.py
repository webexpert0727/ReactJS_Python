# -*- coding: utf-8 -*-

from modeltranslation.translator import register, TranslationOptions
from coffees.models import CoffeeType, BrewMethod, Flavor, CoffeeGear


@register(CoffeeType)
class CoffeeTypeTranslationOptions(TranslationOptions):
    fields = ('maker', 'region', 'taste', 'more_taste',
              'description', 'altitude', 'varietal', 'process')


@register(BrewMethod)
class BrewMethodTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Flavor)
class FlavorTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(CoffeeGear)
class CoffeeGearTranslationOptions(TranslationOptions):
    fields = ('name', 'model', 'description', 'more_info', 'link')
